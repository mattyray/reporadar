"""Celery tasks for GitHub search and repo analysis."""

from datetime import datetime, timezone

from celery import shared_task
from django.db.models import Q
from django.utils import timezone as django_tz

from apps.accounts.models import get_github_token
from apps.prospects.models import (
    Organization,
    OrganizationRepo,
    RepoContributor,
    RepoStackDetection,
)
from apps.search.detection import detect_stack
from apps.search.models import SearchQuery, SearchResult
from apps.search.scoring import calculate_total_score
from providers.github_client import GitHubClient


@shared_task(bind=True)
def scan_search_results(self, search_id: str):
    """Main search task: run GitHub code search, analyze repos, score results."""
    search = SearchQuery.objects.get(id=search_id)
    search.status = "running"
    search.started_at = django_tz.now()
    search.celery_task_id = self.request.id or ""
    search.save(update_fields=["status", "started_at", "celery_task_id"])

    try:
        token = get_github_token(search.user)
        if not token:
            # No GitHub token — search local database (demo data / previously scanned)
            _search_local_database(search)
            return

        client = GitHubClient(token=token)
        config = search.config
        must_have = config.get("stack_requirements", {}).get("must_have", [])
        nice_to_have = config.get("stack_requirements", {}).get("nice_to_have", [])
        ai_signals = config.get("stack_requirements", {}).get("ai_tool_signals", [])
        filters = config.get("filters", {})
        max_results = config.get("max_results", 50)

        # Build search queries from must_have techs
        search_queries = _build_search_queries(must_have, ai_signals, filters)

        seen_repos = set()
        orgs_found = set()

        for query in search_queries:
            results = client.code_search(query, per_page=30)
            for item in results.get("items", []):
                repo_data = item.get("repository", {})
                repo_id = repo_data.get("id")
                if repo_id in seen_repos:
                    continue
                seen_repos.add(repo_id)

                owner = repo_data.get("owner", {})
                if filters.get("org_only") and owner.get("type") != "Organization":
                    continue

                # Analyze this repo
                org, repo = _process_repo(client, owner, repo_data)
                if org:
                    orgs_found.add(org.id)

                    # Score it
                    detected_techs = list(
                        repo.stack_detections.values_list("technology_name", flat=True)
                    )
                    score = calculate_total_score(
                        detected_techs=detected_techs,
                        must_have=must_have,
                        nice_to_have=nice_to_have,
                        has_claude_md=repo.has_claude_md,
                        has_cursor_config=repo.has_cursor_config,
                        has_copilot_config=repo.has_copilot_config,
                        has_windsurf_config=repo.has_windsurf_config,
                        has_docker=repo.has_docker,
                        has_ci_cd=repo.has_ci_cd,
                        has_tests=repo.has_tests,
                        has_deployment_config=repo.has_deployment_config,
                        last_pushed_at=repo.last_pushed_at,
                        contributor_count=repo.contributors.count(),
                    )

                    SearchResult.objects.update_or_create(
                        search=search,
                        repo=repo,
                        defaults={
                            "organization": org,
                            "match_score": score,
                            "matched_stack": detected_techs,
                        },
                    )

                if len(seen_repos) >= max_results:
                    break

            if len(seen_repos) >= max_results:
                break

        search.status = "completed"
        search.total_repos_found = len(seen_repos)
        search.total_orgs_found = len(orgs_found)
        search.completed_at = django_tz.now()
        search.save(update_fields=[
            "status", "total_repos_found", "total_orgs_found", "completed_at"
        ])

    except Exception as e:
        search.status = "failed"
        search.error_message = str(e)
        search.save(update_fields=["status", "error_message"])
        raise


def _search_local_database(search):
    """Search locally cached/seeded organizations instead of GitHub.

    This runs when GitHub isn't connected — matches against orgs already
    in the database (from demo seed data or previous scans).
    """
    config = search.config
    must_have = config.get("stack_requirements", {}).get("must_have", [])
    nice_to_have = config.get("stack_requirements", {}).get("nice_to_have", [])
    max_results = config.get("max_results", 50)

    # Find repos that have any of the must_have technologies
    tech_filter = Q()
    for tech in must_have:
        tech_filter |= Q(stack_detections__technology_name__iexact=tech)

    if tech_filter:
        repos = OrganizationRepo.objects.filter(tech_filter).distinct()[:max_results]
    else:
        repos = OrganizationRepo.objects.all()[:max_results]

    orgs_found = set()
    for repo in repos:
        org = repo.organization
        orgs_found.add(org.id)

        detected_techs = list(
            repo.stack_detections.values_list("technology_name", flat=True)
        )
        score = calculate_total_score(
            detected_techs=detected_techs,
            must_have=must_have,
            nice_to_have=nice_to_have,
            has_claude_md=repo.has_claude_md,
            has_cursor_config=repo.has_cursor_config,
            has_copilot_config=repo.has_copilot_config,
            has_windsurf_config=repo.has_windsurf_config,
            has_docker=repo.has_docker,
            has_ci_cd=repo.has_ci_cd,
            has_tests=repo.has_tests,
            has_deployment_config=repo.has_deployment_config,
            last_pushed_at=repo.last_pushed_at,
            contributor_count=repo.contributors.count(),
        )

        SearchResult.objects.update_or_create(
            search=search,
            repo=repo,
            defaults={
                "organization": org,
                "match_score": score,
                "matched_stack": detected_techs,
            },
        )

    search.status = "completed"
    search.total_repos_found = repos.count()
    search.total_orgs_found = len(orgs_found)
    search.completed_at = django_tz.now()
    search.save(update_fields=[
        "status", "total_repos_found", "total_orgs_found", "completed_at"
    ])


def _build_search_queries(must_have, ai_signals, filters):
    """Build GitHub code search query strings from search config."""
    queries = []

    # Search for dependency files mentioning must_have techs
    for tech in must_have:
        queries.append(f"{tech} filename:requirements.txt")
        queries.append(f"{tech} filename:package.json")

    # Search for AI tool signal files
    signal_file_map = {
        "CLAUDE.md": "filename:CLAUDE.md",
        ".cursor": "path:.cursor",
        ".github/copilot": "filename:copilot-instructions.md",
    }
    for signal in ai_signals:
        query = signal_file_map.get(signal)
        if query:
            queries.append(query)

    return queries if queries else ["filename:requirements.txt"]


def _process_repo(client, owner_data, repo_data):
    """Fetch repo details, detect stack, check signals, pull contributors."""
    owner_login = owner_data.get("login", "")
    repo_name = repo_data.get("name", "")

    # Get or create the organization
    org, _ = Organization.objects.update_or_create(
        github_id=owner_data["id"],
        defaults={
            "github_login": owner_login,
            "name": owner_data.get("name", owner_login),
            "avatar_url": owner_data.get("avatar_url", ""),
            "github_url": f"https://github.com/{owner_login}",
            "last_scanned_at": django_tz.now(),
        },
    )

    # Try to enrich org data
    try:
        org_details = client.get_org(owner_login)
        org.name = org_details.get("name", "") or owner_login
        org.description = org_details.get("description", "") or ""
        org.website = org_details.get("blog", "") or ""
        org.email = org_details.get("email", "") or ""
        org.location = org_details.get("location", "") or ""
        org.public_repos_count = org_details.get("public_repos", 0)
        org.save()
    except Exception:
        pass  # Org details are nice-to-have, not critical

    # Get or create the repo
    pushed_at = None
    if repo_data.get("pushed_at"):
        pushed_at = datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00"))

    created_at_gh = None
    if repo_data.get("created_at"):
        created_at_gh = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))

    repo, _ = OrganizationRepo.objects.update_or_create(
        github_id=repo_data["id"],
        defaults={
            "organization": org,
            "name": repo_name,
            "full_name": repo_data.get("full_name", f"{owner_login}/{repo_name}"),
            "description": repo_data.get("description", "") or "",
            "url": repo_data.get("html_url", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "is_fork": repo_data.get("fork", False),
            "default_branch": repo_data.get("default_branch", "main"),
            "last_pushed_at": pushed_at,
            "created_at_github": created_at_gh,
            "last_scanned_at": django_tz.now(),
        },
    )

    # Detect stack from dependency files
    files = {}
    for dep_file in ["requirements.txt", "pyproject.toml", "package.json"]:
        contents = client.get_file_contents(owner_login, repo_name, dep_file)
        if contents:
            files[dep_file] = contents

    techs = detect_stack(files)
    for tech_name, category in techs:
        RepoStackDetection.objects.update_or_create(
            repo=repo,
            technology_name=tech_name,
            defaults={"category": category, "source_file": "detected"},
        )

    # Check AI tool signals
    repo.has_claude_md = client.check_file_exists(owner_login, repo_name, "CLAUDE.md")
    repo.has_cursor_config = client.check_file_exists(owner_login, repo_name, ".cursor")
    repo.has_copilot_config = client.check_file_exists(
        owner_login, repo_name, ".github/copilot-instructions.md"
    )
    repo.has_windsurf_config = client.check_file_exists(owner_login, repo_name, ".windsurfrules")

    # Check infrastructure signals
    repo.has_docker = (
        client.check_file_exists(owner_login, repo_name, "Dockerfile")
        or client.check_file_exists(owner_login, repo_name, "docker-compose.yml")
    )
    repo.has_ci_cd = client.check_file_exists(owner_login, repo_name, ".github/workflows")
    repo.has_tests = (
        client.check_file_exists(owner_login, repo_name, "tests")
        or client.check_file_exists(owner_login, repo_name, "test")
        or client.check_file_exists(owner_login, repo_name, "pytest.ini")
        or client.check_file_exists(owner_login, repo_name, "conftest.py")
    )
    repo.has_deployment_config = (
        client.check_file_exists(owner_login, repo_name, "Procfile")
        or client.check_file_exists(owner_login, repo_name, "railway.json")
        or client.check_file_exists(owner_login, repo_name, "fly.toml")
        or client.check_file_exists(owner_login, repo_name, "render.yaml")
    )
    repo.save()

    # Pull top 5 contributors
    try:
        contributors = client.get_contributors(owner_login, repo_name, per_page=5)
        for contrib in contributors:
            user_profile = client.get_user(contrib["login"])
            RepoContributor.objects.update_or_create(
                repo=repo,
                github_id=contrib["id"],
                defaults={
                    "github_username": contrib["login"],
                    "name": user_profile.get("name", "") or "",
                    "email": user_profile.get("email", "") or "",
                    "company": user_profile.get("company", "") or "",
                    "bio": user_profile.get("bio", "") or "",
                    "location": user_profile.get("location", "") or "",
                    "blog": user_profile.get("blog", "") or "",
                    "twitter_username": user_profile.get("twitter_username", "") or "",
                    "avatar_url": contrib.get("avatar_url", ""),
                    "contributions": contrib.get("contributions", 0),
                    "profile_url": f"https://github.com/{contrib['login']}",
                    "last_fetched_at": django_tz.now(),
                },
            )
    except Exception:
        pass  # Contributors are nice-to-have

    return org, repo
