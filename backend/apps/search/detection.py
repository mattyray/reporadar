"""Stack detection — pure functions that parse dependency files into detected technologies.

Each function takes file contents (string) and returns a list of (technology_name, category) tuples.
No database access, no API calls — just parsing.
"""

import json
import re


def detect_from_requirements_txt(contents: str) -> list[tuple[str, str]]:
    """Parse requirements.txt format (pip freeze style)."""
    techs = []
    for line in contents.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name (before any version specifier)
        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
        if not match:
            continue
        pkg = match.group(1).lower()
        detected = PYTHON_PACKAGE_MAP.get(pkg)
        if detected:
            techs.append(detected)
    return techs


def detect_from_pyproject_toml(contents: str) -> list[tuple[str, str]]:
    """Parse pyproject.toml for dependencies."""
    techs = []
    in_deps = False
    for line in contents.splitlines():
        stripped = line.strip()
        # Look for dependencies sections
        if stripped in ("[project.dependencies]", "dependencies = ["):
            in_deps = True
            continue
        if in_deps:
            if stripped.startswith("[") and not stripped.startswith('"'):
                in_deps = False
                continue
            if stripped == "]":
                in_deps = False
                continue
            # Extract package name from quoted strings like "django>=5.0"
            match = re.match(r'["\']?([a-zA-Z0-9_-]+)', stripped)
            if match:
                pkg = match.group(1).lower()
                detected = PYTHON_PACKAGE_MAP.get(pkg)
                if detected:
                    techs.append(detected)
    return techs


def detect_from_package_json(contents: str) -> list[tuple[str, str]]:
    """Parse package.json for dependencies."""
    techs = []
    try:
        data = json.loads(contents)
    except json.JSONDecodeError:
        return techs
    all_deps = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))
    for pkg in all_deps:
        pkg_lower = pkg.lower()
        detected = JS_PACKAGE_MAP.get(pkg_lower)
        if detected:
            techs.append(detected)
    return techs


def detect_stack(files: dict[str, str]) -> list[tuple[str, str]]:
    """Main entry point: given a dict of {filename: contents}, detect all technologies.

    Args:
        files: dict mapping filename (e.g. "requirements.txt") to file contents string.

    Returns:
        Deduplicated list of (technology_name, category) tuples.
    """
    techs = []

    # Python detection (check in priority order)
    for filename in ["requirements.txt", "requirements/base.txt", "requirements/production.txt"]:
        if filename in files:
            techs.extend(detect_from_requirements_txt(files[filename]))
            break

    if "pyproject.toml" in files:
        techs.extend(detect_from_pyproject_toml(files["pyproject.toml"]))

    # JavaScript/TypeScript detection
    for filename in ["package.json", "frontend/package.json", "client/package.json", "web/package.json"]:
        if filename in files:
            techs.extend(detect_from_package_json(files[filename]))

    # Deduplicate by technology name
    seen = set()
    unique_techs = []
    for tech_name, category in techs:
        if tech_name not in seen:
            seen.add(tech_name)
            unique_techs.append((tech_name, category))

    return unique_techs


# --- Package name → (technology_name, category) mappings ---

PYTHON_PACKAGE_MAP = {
    # Backend frameworks
    "django": ("Django", "backend"),
    "flask": ("Flask", "backend"),
    "fastapi": ("FastAPI", "backend"),
    "starlette": ("Starlette", "backend"),
    "tornado": ("Tornado", "backend"),
    "sanic": ("Sanic", "backend"),
    # Django ecosystem
    "djangorestframework": ("Django REST Framework", "backend"),
    "django-ninja": ("Django Ninja", "backend"),
    "celery": ("Celery", "backend"),
    "django-allauth": ("django-allauth", "backend"),
    "channels": ("Django Channels", "backend"),
    # Databases
    "psycopg2": ("PostgreSQL", "database"),
    "psycopg2-binary": ("PostgreSQL", "database"),
    "psycopg": ("PostgreSQL", "database"),
    "mysqlclient": ("MySQL", "database"),
    "pymongo": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "sqlalchemy": ("SQLAlchemy", "database"),
    # AI/ML
    "langchain": ("LangChain", "ai_ml"),
    "langchain-core": ("LangChain", "ai_ml"),
    "langgraph": ("LangGraph", "ai_ml"),
    "anthropic": ("Claude API", "ai_ml"),
    "openai": ("OpenAI API", "ai_ml"),
    "transformers": ("Hugging Face Transformers", "ai_ml"),
    "torch": ("PyTorch", "ai_ml"),
    "tensorflow": ("TensorFlow", "ai_ml"),
    "scikit-learn": ("scikit-learn", "ai_ml"),
    "numpy": ("NumPy", "ai_ml"),
    "pandas": ("pandas", "ai_ml"),
    # Infrastructure
    "gunicorn": ("Gunicorn", "infrastructure"),
    "uvicorn": ("Uvicorn", "infrastructure"),
    "boto3": ("AWS SDK", "infrastructure"),
    "google-cloud-storage": ("Google Cloud", "infrastructure"),
    "sentry-sdk": ("Sentry", "infrastructure"),
}

JS_PACKAGE_MAP = {
    # Frontend frameworks
    "react": ("React", "frontend"),
    "react-dom": ("React", "frontend"),
    "next": ("Next.js", "frontend"),
    "vue": ("Vue.js", "frontend"),
    "nuxt": ("Nuxt.js", "frontend"),
    "svelte": ("Svelte", "frontend"),
    "@angular/core": ("Angular", "frontend"),
    "solid-js": ("Solid.js", "frontend"),
    # TypeScript
    "typescript": ("TypeScript", "frontend"),
    # Styling
    "tailwindcss": ("Tailwind CSS", "frontend"),
    # State management
    "redux": ("Redux", "frontend"),
    "@tanstack/react-query": ("TanStack Query", "frontend"),
    "zustand": ("Zustand", "frontend"),
    # Backend (Node)
    "express": ("Express.js", "backend"),
    "fastify": ("Fastify", "backend"),
    "nestjs": ("NestJS", "backend"),
    "@nestjs/core": ("NestJS", "backend"),
    "hono": ("Hono", "backend"),
    # Databases
    "prisma": ("Prisma", "database"),
    "@prisma/client": ("Prisma", "database"),
    "mongoose": ("MongoDB", "database"),
    "pg": ("PostgreSQL", "database"),
    "mysql2": ("MySQL", "database"),
    "drizzle-orm": ("Drizzle ORM", "database"),
    # AI
    "langchain": ("LangChain", "ai_ml"),
    "@langchain/core": ("LangChain", "ai_ml"),
    "openai": ("OpenAI API", "ai_ml"),
    "@anthropic-ai/sdk": ("Claude API", "ai_ml"),
    "ai": ("Vercel AI SDK", "ai_ml"),
    # Build tools
    "vite": ("Vite", "infrastructure"),
    "webpack": ("Webpack", "infrastructure"),
    "esbuild": ("esbuild", "infrastructure"),
    # Testing
    "jest": ("Jest", "infrastructure"),
    "vitest": ("Vitest", "infrastructure"),
    "@testing-library/react": ("React Testing Library", "infrastructure"),
    "cypress": ("Cypress", "infrastructure"),
    "playwright": ("Playwright", "infrastructure"),
}
