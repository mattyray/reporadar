"""Celery task for AI-powered repo analysis using Claude API."""

import json
import logging
import os

import anthropic
from celery import shared_task
from django.utils import timezone

from apps.accounts.models import get_github_token
from providers.github_client import GitHubClient

logger = logging.getLogger(__name__)

# Files worth fetching for deep analysis (in priority order)
ANALYSIS_FILES = [
    "README.md",
    "readme.md",
    "README.rst",
    # Dependency files
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "composer.json",
    # Config / infra
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows/ci.yml",
    ".github/workflows/ci.yaml",
    ".github/workflows/main.yml",
    "Procfile",
    "railway.json",
    "fly.toml",
    "render.yaml",
    "netlify.toml",
    "vercel.json",
    # Project config
    "tsconfig.json",
    ".env.example",
    "Makefile",
    # AI tool configs
    "CLAUDE.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    # Entry points (try common ones)
    "main.py",
    "app.py",
    "manage.py",
    "index.ts",
    "index.js",
    "src/index.ts",
    "src/index.js",
    "src/main.ts",
    "src/main.tsx",
    "src/app.py",
    "cmd/main.go",
    "main.go",
]

# Max characters per file to avoid blowing up context
MAX_FILE_CHARS = 8000
# Max total chars for all files combined
MAX_TOTAL_CHARS = 60000


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def analyze_repo_with_ai(self, repo_id: int, user_id: int):
    """Fetch repo files and directory tree, send to Claude for deep analysis."""
    from apps.prospects.models import OrganizationRepo

    repo = OrganizationRepo.objects.select_related("organization").get(pk=repo_id)

    # Mark as analyzing
    repo.ai_analysis_status = "analyzing"
    repo.ai_analysis_error = ""
    repo.save(update_fields=["ai_analysis_status", "ai_analysis_error"])

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")

        # Get GitHub token for this user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        token = get_github_token(user)
        if not token:
            raise RuntimeError("GitHub not connected — cannot fetch repo files")

        client = GitHubClient(token=token)
        owner = repo.organization.github_login
        repo_name = repo.name

        # 1. Fetch directory tree
        tree_paths = client.get_repo_tree(owner, repo_name, repo.default_branch)
        tree_summary = _build_tree_summary(tree_paths)

        # 2. Fetch key files
        fetched_files = {}
        total_chars = 0
        for file_path in ANALYSIS_FILES:
            if total_chars >= MAX_TOTAL_CHARS:
                break
            contents = client.get_file_contents(owner, repo_name, file_path)
            if contents:
                truncated = contents[:MAX_FILE_CHARS]
                fetched_files[file_path] = truncated
                total_chars += len(truncated)

        # 3. Build prompt and call Claude
        prompt = _build_analysis_prompt(
            repo_full_name=repo.full_name,
            description=repo.description,
            stars=repo.stars,
            forks=repo.forks,
            tree_summary=tree_summary,
            files=fetched_files,
        )

        claude = anthropic.Anthropic(api_key=api_key)
        message = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            analysis = json.loads(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            raise RuntimeError("Claude returned invalid JSON for repo analysis")

        # 4. Save analysis
        repo.ai_analysis = analysis
        repo.ai_analysis_status = "completed"
        repo.ai_analysis_error = ""
        repo.ai_analyzed_at = timezone.now()
        repo.save(update_fields=[
            "ai_analysis", "ai_analysis_status", "ai_analysis_error", "ai_analyzed_at",
        ])

        return {"status": "completed", "repo_id": repo_id}

    except Exception as e:
        logger.exception(f"AI analysis failed for repo {repo_id}: {e}")
        repo.ai_analysis_status = "failed"
        repo.ai_analysis_error = str(e)
        repo.save(update_fields=["ai_analysis_status", "ai_analysis_error"])

        # Retry on transient errors
        import requests as req_lib
        if self.request.retries < self.max_retries and isinstance(
            e, (req_lib.ConnectionError, req_lib.Timeout, anthropic.APIConnectionError)
        ):
            self.retry(exc=e)

        raise


def _build_tree_summary(paths: list[str]) -> str:
    """Build a condensed directory tree from a list of file paths.

    Shows top-level structure and first 2 levels of nesting, with file
    counts for deeper directories. This keeps the tree readable without
    overwhelming Claude's context.
    """
    if not paths:
        return "(empty or inaccessible)"

    # Group by top-level directory
    top_level = {}
    root_files = []

    for path in paths:
        parts = path.split("/")
        if len(parts) == 1:
            root_files.append(path)
        else:
            top_dir = parts[0]
            if top_dir not in top_level:
                top_level[top_dir] = []
            top_level[top_dir].append("/".join(parts[1:]))

    lines = []

    # Root files
    for f in sorted(root_files):
        lines.append(f)

    # Directories with contents summary
    for dir_name in sorted(top_level.keys()):
        children = top_level[dir_name]
        sub_files = [c for c in children if "/" not in c]
        sub_dirs = set(c.split("/")[0] for c in children if "/" in c)

        lines.append(f"{dir_name}/")
        for sf in sorted(sub_files)[:10]:
            lines.append(f"  {sf}")
        if len(sub_files) > 10:
            lines.append(f"  ... and {len(sub_files) - 10} more files")
        for sd in sorted(sub_dirs):
            count = sum(1 for c in children if c.startswith(sd + "/") or c == sd)
            lines.append(f"  {sd}/ ({count} items)")

    # Cap total output
    if len(lines) > 200:
        lines = lines[:200]
        lines.append(f"... ({len(paths)} total files)")

    return "\n".join(lines)


def _build_analysis_prompt(
    repo_full_name: str,
    description: str,
    stars: int,
    forks: int,
    tree_summary: str,
    files: dict[str, str],
) -> str:
    """Build the Claude prompt for deep repo analysis."""

    files_section = ""
    for path, content in files.items():
        files_section += f"\n--- {path} ---\n{content}\n"

    return f"""Analyze this GitHub repository and provide a detailed breakdown. Return ONLY valid JSON.

REPOSITORY: {repo_full_name}
DESCRIPTION: {description or 'No description provided'}
STARS: {stars} | FORKS: {forks}

DIRECTORY STRUCTURE:
{tree_summary}

FILE CONTENTS:
{files_section}

Return this JSON structure (fill in every field, use null if truly unknown):

{{
  "summary": "2-4 sentence plain English explanation of what this project does, who it's for, and what problem it solves",
  "tech_stack": {{
    "languages": ["Python", "TypeScript"],
    "frameworks": ["Django", "React"],
    "databases": ["PostgreSQL"],
    "infrastructure": ["Docker", "GitHub Actions"],
    "notable_libraries": ["Celery", "TanStack Query"],
    "ai_tools": ["Claude Code", "Cursor"]
  }},
  "architecture": {{
    "pattern": "Monolith with REST API backend and SPA frontend",
    "description": "1-3 sentence explanation of the architectural approach and why it makes sense for this project",
    "key_directories": [
      {{"path": "src/", "purpose": "Main application source code"}},
      {{"path": "tests/", "purpose": "Test suite"}}
    ]
  }},
  "code_quality": {{
    "has_tests": true,
    "has_ci_cd": true,
    "has_linting": false,
    "has_type_checking": true,
    "has_documentation": true,
    "quality_notes": "Brief notes on code quality signals observed"
  }},
  "maturity": {{
    "stage": "Production / MVP / Prototype / Experiment / Boilerplate",
    "signals": ["Deployed on Railway", "Has CI/CD pipeline", "Has test suite"],
    "team_size_estimate": "Solo developer / Small team (2-5) / Medium team (5-15) / Large team",
    "activity_assessment": "Actively developed / Maintained / Stale / Abandoned"
  }},
  "what_they_are_building": "1-2 sentence insight into the product direction, inferred from recent code, TODOs, roadmap files, or feature branches",
  "notable_patterns": [
    "Uses TDD with pytest",
    "Provider-agnostic adapter pattern for external APIs",
    "Celery for background job processing"
  ],
  "interesting_for_job_seekers": {{
    "why_work_here": "1-2 sentences on why an engineer might want to work on this project",
    "tech_culture_signals": ["Uses AI coding tools", "Has thorough testing", "Modern stack"],
    "potential_roles": ["Backend Engineer", "Full-Stack Engineer"]
  }}
}}

RULES:
- Be specific: "Django 5 with DRF" not just "Python web framework"
- tech_stack.notable_libraries: include specific libraries you see in dependency files (e.g. "Celery", "pandas", "Prisma")
- architecture.key_directories: list the 3-8 most important directories and what they contain
- Be honest about maturity — don't oversell a weekend project as production-grade
- what_they_are_building: infer from code, not just the README description
- Return ONLY the JSON object, no markdown code fences, no explanation"""
