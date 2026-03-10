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


# --- GitHub language field → (technology_name, category) ---
# Used as fallback when no dependency file is found for that language.
GITHUB_LANGUAGE_MAP = {
    "Python": ("Python", "backend"),
    "JavaScript": ("JavaScript", "frontend"),
    "TypeScript": ("TypeScript", "frontend"),
    "Go": ("Go", "backend"),
    "Rust": ("Rust", "backend"),
    "Java": ("Java", "backend"),
    "Kotlin": ("Kotlin", "backend"),
    "Ruby": ("Ruby", "backend"),
    "PHP": ("PHP", "backend"),
    "C#": ("C#", "backend"),
    "Swift": ("Swift", "backend"),
    "Dart": ("Dart", "frontend"),
    "Elixir": ("Elixir", "backend"),
    "Scala": ("Scala", "backend"),
    "Clojure": ("Clojure", "backend"),
    "Haskell": ("Haskell", "backend"),
    "Lua": ("Lua", "backend"),
    "R": ("R", "ai_ml"),
    "Julia": ("Julia", "ai_ml"),
    "C": ("C", "backend"),
    "C++": ("C++", "backend"),
    "Shell": ("Shell", "infrastructure"),
    "HCL": ("Terraform", "infrastructure"),
    "Nix": ("Nix", "infrastructure"),
    "Zig": ("Zig", "backend"),
}

# --- GitHub topics → (technology_name, category) ---
# Repos often tag themselves with topics like "django", "react", etc.
GITHUB_TOPIC_MAP = {
    # Python frameworks
    "django": ("Django", "backend"),
    "flask": ("Flask", "backend"),
    "fastapi": ("FastAPI", "backend"),
    "celery": ("Celery", "backend"),
    # JS frameworks
    "react": ("React", "frontend"),
    "reactjs": ("React", "frontend"),
    "nextjs": ("Next.js", "frontend"),
    "next-js": ("Next.js", "frontend"),
    "vue": ("Vue.js", "frontend"),
    "vuejs": ("Vue.js", "frontend"),
    "nuxt": ("Nuxt.js", "frontend"),
    "nuxtjs": ("Nuxt.js", "frontend"),
    "svelte": ("Svelte", "frontend"),
    "angular": ("Angular", "frontend"),
    "remix": ("Remix", "frontend"),
    "astro": ("Astro", "frontend"),
    "typescript": ("TypeScript", "frontend"),
    "tailwindcss": ("Tailwind CSS", "frontend"),
    "tailwind": ("Tailwind CSS", "frontend"),
    # Backend / Node
    "express": ("Express.js", "backend"),
    "expressjs": ("Express.js", "backend"),
    "nestjs": ("NestJS", "backend"),
    "fastify": ("Fastify", "backend"),
    "graphql": ("GraphQL", "backend"),
    "trpc": ("tRPC", "backend"),
    # Go
    "golang": ("Go", "backend"),
    "gin": ("Gin", "backend"),
    "echo": ("Echo", "backend"),
    "fiber": ("Fiber", "backend"),
    # Rust
    "rust": ("Rust", "backend"),
    "actix": ("Actix Web", "backend"),
    "tokio": ("Tokio", "backend"),
    # Ruby
    "rails": ("Ruby on Rails", "backend"),
    "ruby-on-rails": ("Ruby on Rails", "backend"),
    "sinatra": ("Sinatra", "backend"),
    # Java / JVM
    "spring": ("Spring", "backend"),
    "spring-boot": ("Spring Boot", "backend"),
    "kotlin": ("Kotlin", "backend"),
    # PHP
    "laravel": ("Laravel", "backend"),
    "symfony": ("Symfony", "backend"),
    # Databases
    "postgresql": ("PostgreSQL", "database"),
    "postgres": ("PostgreSQL", "database"),
    "mongodb": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "mysql": ("MySQL", "database"),
    "elasticsearch": ("Elasticsearch", "database"),
    "supabase": ("Supabase", "database"),
    "prisma": ("Prisma", "database"),
    "sqlite": ("SQLite", "database"),
    # AI/ML
    "openai": ("OpenAI API", "ai_ml"),
    "gpt": ("OpenAI API", "ai_ml"),
    "langchain": ("LangChain", "ai_ml"),
    "llm": ("LLM", "ai_ml"),
    "large-language-model": ("LLM", "ai_ml"),
    "claude": ("Claude API", "ai_ml"),
    "anthropic": ("Claude API", "ai_ml"),
    "machine-learning": ("Machine Learning", "ai_ml"),
    "deep-learning": ("Deep Learning", "ai_ml"),
    "pytorch": ("PyTorch", "ai_ml"),
    "tensorflow": ("TensorFlow", "ai_ml"),
    "huggingface": ("Hugging Face", "ai_ml"),
    "transformers": ("Hugging Face Transformers", "ai_ml"),
    "computer-vision": ("Computer Vision", "ai_ml"),
    "nlp": ("NLP", "ai_ml"),
    "rag": ("RAG", "ai_ml"),
    "vector-database": ("Vector DB", "ai_ml"),
    "embeddings": ("Embeddings", "ai_ml"),
    # Infrastructure
    "docker": ("Docker", "infrastructure"),
    "kubernetes": ("Kubernetes", "infrastructure"),
    "k8s": ("Kubernetes", "infrastructure"),
    "terraform": ("Terraform", "infrastructure"),
    "aws": ("AWS", "infrastructure"),
    "gcp": ("Google Cloud", "infrastructure"),
    "azure": ("Azure", "infrastructure"),
    "serverless": ("Serverless", "infrastructure"),
    "ci-cd": ("CI/CD", "infrastructure"),
    "github-actions": ("GitHub Actions", "infrastructure"),
    # AI Tools
    "cursor": ("Cursor", "ai_tool"),
    "claude-code": ("Claude Code", "ai_tool"),
    "copilot": ("GitHub Copilot", "ai_tool"),
    "ai-assisted": ("AI-Assisted", "ai_tool"),
    "ai-coding": ("AI-Assisted", "ai_tool"),
}


# --- Package name → (technology_name, category) mappings ---

PYTHON_PACKAGE_MAP = {
    # Backend frameworks
    "django": ("Django", "backend"),
    "flask": ("Flask", "backend"),
    "fastapi": ("FastAPI", "backend"),
    "starlette": ("Starlette", "backend"),
    "tornado": ("Tornado", "backend"),
    "sanic": ("Sanic", "backend"),
    "pydantic": ("Pydantic", "backend"),
    "httpx": ("HTTPX", "backend"),
    # Django ecosystem
    "djangorestframework": ("Django REST Framework", "backend"),
    "django-ninja": ("Django Ninja", "backend"),
    "celery": ("Celery", "backend"),
    "django-allauth": ("django-allauth", "backend"),
    "channels": ("Django Channels", "backend"),
    # Auth
    "auth0-python": ("Auth0", "backend"),
    "pyjwt": ("JWT Auth", "backend"),
    "python-jose": ("JWT Auth", "backend"),
    "python-keycloak": ("Keycloak", "backend"),
    "firebase-admin": ("Firebase", "backend"),
    # Payments
    "stripe": ("Stripe", "backend"),
    # Databases
    "psycopg2": ("PostgreSQL", "database"),
    "psycopg2-binary": ("PostgreSQL", "database"),
    "psycopg": ("PostgreSQL", "database"),
    "asyncpg": ("PostgreSQL", "database"),
    "mysqlclient": ("MySQL", "database"),
    "pymongo": ("MongoDB", "database"),
    "motor": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "aioredis": ("Redis", "database"),
    "sqlalchemy": ("SQLAlchemy", "database"),
    "alembic": ("Alembic", "database"),
    "tortoise-orm": ("Tortoise ORM", "database"),
    "peewee": ("Peewee", "database"),
    "elasticsearch": ("Elasticsearch", "database"),
    "opensearch-py": ("OpenSearch", "database"),
    "cassandra-driver": ("Cassandra", "database"),
    "neo4j": ("Neo4j", "database"),
    "clickhouse-connect": ("ClickHouse", "database"),
    "supabase": ("Supabase", "database"),
    # AI/ML
    "langchain": ("LangChain", "ai_ml"),
    "langchain-core": ("LangChain", "ai_ml"),
    "langgraph": ("LangGraph", "ai_ml"),
    "anthropic": ("Claude API", "ai_ml"),
    "openai": ("OpenAI API", "ai_ml"),
    "transformers": ("Hugging Face Transformers", "ai_ml"),
    "huggingface-hub": ("Hugging Face Hub", "ai_ml"),
    "datasets": ("Hugging Face Datasets", "ai_ml"),
    "accelerate": ("Hugging Face Accelerate", "ai_ml"),
    "torch": ("PyTorch", "ai_ml"),
    "tensorflow": ("TensorFlow", "ai_ml"),
    "scikit-learn": ("scikit-learn", "ai_ml"),
    "numpy": ("NumPy", "ai_ml"),
    "pandas": ("pandas", "ai_ml"),
    "llama-index": ("LlamaIndex", "ai_ml"),
    "llama-index-core": ("LlamaIndex", "ai_ml"),
    "chromadb": ("ChromaDB", "ai_ml"),
    "pinecone-client": ("Pinecone", "ai_ml"),
    "pinecone": ("Pinecone", "ai_ml"),
    "weaviate-client": ("Weaviate", "ai_ml"),
    "qdrant-client": ("Qdrant", "ai_ml"),
    "pgvector": ("pgvector", "ai_ml"),
    "faiss-cpu": ("FAISS", "ai_ml"),
    "faiss-gpu": ("FAISS", "ai_ml"),
    "lancedb": ("LanceDB", "ai_ml"),
    "sentence-transformers": ("Sentence Transformers", "ai_ml"),
    "instructor": ("Instructor", "ai_ml"),
    "outlines": ("Outlines", "ai_ml"),
    "dspy-ai": ("DSPy", "ai_ml"),
    "dspy": ("DSPy", "ai_ml"),
    "crewai": ("CrewAI", "ai_ml"),
    "autogen": ("AutoGen", "ai_ml"),
    "pyautogen": ("AutoGen", "ai_ml"),
    "litellm": ("LiteLLM", "ai_ml"),
    "vllm": ("vLLM", "ai_ml"),
    "ollama": ("Ollama", "ai_ml"),
    "groq": ("Groq API", "ai_ml"),
    "google-generativeai": ("Google Gemini", "ai_ml"),
    "cohere": ("Cohere API", "ai_ml"),
    "replicate": ("Replicate", "ai_ml"),
    "tiktoken": ("tiktoken", "ai_ml"),
    "mlflow": ("MLflow", "ai_ml"),
    "wandb": ("Weights & Biases", "ai_ml"),
    "unstructured": ("Unstructured", "ai_ml"),
    # Infrastructure
    "gunicorn": ("Gunicorn", "infrastructure"),
    "uvicorn": ("Uvicorn", "infrastructure"),
    "boto3": ("AWS SDK", "infrastructure"),
    "google-cloud-storage": ("Google Cloud", "infrastructure"),
    "sentry-sdk": ("Sentry", "infrastructure"),
    "docker": ("Docker", "infrastructure"),
    "pulumi": ("Pulumi", "infrastructure"),
    "aws-cdk-lib": ("AWS CDK", "infrastructure"),
    "cdktf": ("Terraform CDK", "infrastructure"),
    "mangum": ("AWS Lambda", "infrastructure"),
    "aws-lambda-powertools": ("AWS Lambda", "infrastructure"),
    "chalice": ("AWS Chalice", "infrastructure"),
    "functions-framework": ("Google Cloud Functions", "infrastructure"),
    # Observability
    "ddtrace": ("Datadog", "infrastructure"),
    "datadog": ("Datadog", "infrastructure"),
    "newrelic": ("New Relic", "infrastructure"),
    "opentelemetry-api": ("OpenTelemetry", "infrastructure"),
    "opentelemetry-sdk": ("OpenTelemetry", "infrastructure"),
    "prometheus-client": ("Prometheus", "infrastructure"),
    "structlog": ("structlog", "infrastructure"),
    # Testing
    "pytest": ("pytest", "infrastructure"),
    "hypothesis": ("Hypothesis", "infrastructure"),
    "locust": ("Locust", "infrastructure"),
    "factory-boy": ("factory_boy", "infrastructure"),
    "responses": ("responses", "infrastructure"),
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
    "@remix-run/react": ("Remix", "frontend"),
    "astro": ("Astro", "frontend"),
    "three": ("Three.js", "frontend"),
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
    "@trpc/server": ("tRPC", "backend"),
    "socket.io": ("Socket.IO", "backend"),
    "passport": ("Passport.js", "backend"),
    # Auth
    "@auth0/nextjs-auth0": ("Auth0", "backend"),
    "auth0": ("Auth0", "backend"),
    "@clerk/nextjs": ("Clerk", "backend"),
    "@clerk/clerk-react": ("Clerk", "backend"),
    "next-auth": ("NextAuth.js", "backend"),
    "@auth/core": ("Auth.js", "backend"),
    "lucia": ("Lucia Auth", "backend"),
    "@kinde-oss/kinde-auth-nextjs": ("Kinde", "backend"),
    "firebase": ("Firebase", "backend"),
    "firebase-admin": ("Firebase", "backend"),
    # Payments
    "stripe": ("Stripe", "backend"),
    "@stripe/stripe-js": ("Stripe", "backend"),
    "@stripe/react-stripe-js": ("Stripe", "backend"),
    "@lemonsqueezy/lemonsqueezy.js": ("Lemon Squeezy", "backend"),
    # Databases
    "prisma": ("Prisma", "database"),
    "@prisma/client": ("Prisma", "database"),
    "mongoose": ("MongoDB", "database"),
    "pg": ("PostgreSQL", "database"),
    "mysql2": ("MySQL", "database"),
    "drizzle-orm": ("Drizzle ORM", "database"),
    "typeorm": ("TypeORM", "database"),
    "@mikro-orm/core": ("MikroORM", "database"),
    "sequelize": ("Sequelize", "database"),
    "knex": ("Knex.js", "database"),
    "kysely": ("Kysely", "database"),
    "@supabase/supabase-js": ("Supabase", "database"),
    "ioredis": ("Redis", "database"),
    "@upstash/redis": ("Upstash Redis", "database"),
    "@elastic/elasticsearch": ("Elasticsearch", "database"),
    "@neondatabase/serverless": ("Neon", "database"),
    "@planetscale/database": ("PlanetScale", "database"),
    # AI
    "langchain": ("LangChain", "ai_ml"),
    "@langchain/core": ("LangChain", "ai_ml"),
    "openai": ("OpenAI API", "ai_ml"),
    "@anthropic-ai/sdk": ("Claude API", "ai_ml"),
    "ai": ("Vercel AI SDK", "ai_ml"),
    "llamaindex": ("LlamaIndex", "ai_ml"),
    "chromadb": ("ChromaDB", "ai_ml"),
    "@pinecone-database/pinecone": ("Pinecone", "ai_ml"),
    "weaviate-ts-client": ("Weaviate", "ai_ml"),
    "@qdrant/js-client-rest": ("Qdrant", "ai_ml"),
    "@google/generative-ai": ("Google Gemini", "ai_ml"),
    "groq-sdk": ("Groq API", "ai_ml"),
    "cohere-ai": ("Cohere API", "ai_ml"),
    "replicate": ("Replicate", "ai_ml"),
    "ollama": ("Ollama", "ai_ml"),
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
    "msw": ("Mock Service Worker", "infrastructure"),
    "@storybook/react": ("Storybook", "infrastructure"),
    "storybook": ("Storybook", "infrastructure"),
    # Observability
    "@sentry/node": ("Sentry", "infrastructure"),
    "@sentry/react": ("Sentry", "infrastructure"),
    "@sentry/nextjs": ("Sentry", "infrastructure"),
    "dd-trace": ("Datadog", "infrastructure"),
    "newrelic": ("New Relic", "infrastructure"),
    "@opentelemetry/api": ("OpenTelemetry", "infrastructure"),
    "@opentelemetry/sdk-node": ("OpenTelemetry", "infrastructure"),
    "pino": ("Pino", "infrastructure"),
    "winston": ("Winston", "infrastructure"),
    # Cloud/Serverless
    "sst": ("SST", "infrastructure"),
    "@pulumi/pulumi": ("Pulumi", "infrastructure"),
    "aws-cdk-lib": ("AWS CDK", "infrastructure"),
    "serverless": ("Serverless Framework", "infrastructure"),
    "wrangler": ("Cloudflare Workers", "infrastructure"),
    "@cloudflare/workers-types": ("Cloudflare Workers", "infrastructure"),
    "@vercel/kv": ("Vercel KV", "infrastructure"),
    "@vercel/postgres": ("Vercel Postgres", "infrastructure"),
}
