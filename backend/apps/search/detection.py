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


def detect_from_go_mod(contents: str) -> list[tuple[str, str]]:
    """Parse go.mod for require blocks."""
    techs = []
    in_require = False
    for line in contents.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if stripped == ")" and in_require:
            in_require = False
            continue
        if stripped.startswith("require ") and "(" not in stripped:
            # Single-line require
            mod = stripped.split()[1] if len(stripped.split()) > 1 else ""
            detected = _lookup_go_module(mod)
            if detected:
                techs.append(detected)
            continue
        if in_require:
            parts = stripped.split()
            if parts:
                detected = _lookup_go_module(parts[0])
                if detected:
                    techs.append(detected)
    return techs


def _lookup_go_module(mod_path: str) -> tuple[str, str] | None:
    """Look up a Go module path in the package map."""
    # Try exact match first, then progressively shorter prefixes
    if mod_path in GO_MODULE_MAP:
        return GO_MODULE_MAP[mod_path]
    # Try matching the first 2-3 segments (e.g. github.com/gin-gonic/gin)
    parts = mod_path.split("/")
    for length in range(len(parts), 0, -1):
        prefix = "/".join(parts[:length])
        if prefix in GO_MODULE_MAP:
            return GO_MODULE_MAP[prefix]
    return None


def detect_from_cargo_toml(contents: str) -> list[tuple[str, str]]:
    """Parse Cargo.toml [dependencies] section."""
    techs = []
    in_deps = False
    for line in contents.splitlines():
        stripped = line.strip()
        if stripped == "[dependencies]":
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps and "=" in stripped:
            crate = stripped.split("=")[0].strip().strip('"')
            detected = RUST_CRATE_MAP.get(crate)
            if detected:
                techs.append(detected)
    return techs


def detect_from_gemfile(contents: str) -> list[tuple[str, str]]:
    """Parse Gemfile for gem declarations."""
    techs = []
    for line in contents.splitlines():
        stripped = line.strip()
        if not stripped.startswith("gem "):
            continue
        match = re.match(r"""gem\s+['"]([a-zA-Z0-9_-]+)['"]""", stripped)
        if match:
            gem = match.group(1).lower()
            detected = RUBY_GEM_MAP.get(gem)
            if detected:
                techs.append(detected)
    return techs


def detect_from_pom_xml(contents: str) -> list[tuple[str, str]]:
    """Parse pom.xml for Maven dependencies (regex, no XML parser needed)."""
    techs = []
    # Match <artifactId>...</artifactId> within <dependency> blocks
    for match in re.finditer(r"<artifactId>([^<]+)</artifactId>", contents):
        artifact = match.group(1).lower()
        detected = JAVA_ARTIFACT_MAP.get(artifact)
        if detected:
            techs.append(detected)
    return techs


def detect_from_build_gradle(contents: str) -> list[tuple[str, str]]:
    """Parse build.gradle for dependencies."""
    techs = []
    # Match patterns like: implementation 'group:artifact:version'
    for match in re.finditer(
        r"""(?:implementation|api|compile|runtimeOnly)\s+['"]([^'"]+)['"]""", contents
    ):
        dep = match.group(1)
        parts = dep.split(":")
        if len(parts) >= 2:
            artifact = parts[1].lower()
            detected = JAVA_ARTIFACT_MAP.get(artifact)
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

    # Go detection
    for filename in ["go.mod", "backend/go.mod", "app/go.mod"]:
        if filename in files:
            techs.extend(detect_from_go_mod(files[filename]))

    # Rust detection
    for filename in ["Cargo.toml", "backend/Cargo.toml"]:
        if filename in files:
            techs.extend(detect_from_cargo_toml(files[filename]))

    # Ruby detection
    for filename in ["Gemfile", "backend/Gemfile"]:
        if filename in files:
            techs.extend(detect_from_gemfile(files[filename]))

    # Java detection
    for filename in ["pom.xml", "backend/pom.xml", "app/pom.xml"]:
        if filename in files:
            techs.extend(detect_from_pom_xml(files[filename]))
    for filename in ["build.gradle", "build.gradle.kts", "app/build.gradle", "app/build.gradle.kts"]:
        if filename in files:
            techs.extend(detect_from_build_gradle(files[filename]))

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

GO_MODULE_MAP = {
    # Web frameworks
    "github.com/gin-gonic/gin": ("Gin", "backend"),
    "github.com/labstack/echo": ("Echo", "backend"),
    "github.com/gofiber/fiber": ("Fiber", "backend"),
    "github.com/gorilla/mux": ("Gorilla Mux", "backend"),
    "github.com/go-chi/chi": ("Chi", "backend"),
    "github.com/julienschmidt/httprouter": ("httprouter", "backend"),
    # gRPC
    "google.golang.org/grpc": ("gRPC", "backend"),
    "google.golang.org/protobuf": ("Protocol Buffers", "backend"),
    # Databases
    "github.com/lib/pq": ("PostgreSQL", "database"),
    "github.com/jackc/pgx": ("PostgreSQL", "database"),
    "github.com/go-sql-driver/mysql": ("MySQL", "database"),
    "go.mongodb.org/mongo-driver": ("MongoDB", "database"),
    "github.com/go-redis/redis": ("Redis", "database"),
    "github.com/redis/go-redis": ("Redis", "database"),
    "gorm.io/gorm": ("GORM", "database"),
    "github.com/jmoiron/sqlx": ("sqlx", "database"),
    "entgo.io/ent": ("Ent ORM", "database"),
    "github.com/uptrace/bun": ("Bun ORM", "database"),
    # AI
    "github.com/sashabaranov/go-openai": ("OpenAI API", "ai_ml"),
    "github.com/tmc/langchaingo": ("LangChain (Go)", "ai_ml"),
    # Infrastructure
    "github.com/aws/aws-sdk-go-v2": ("AWS SDK", "infrastructure"),
    "github.com/docker/docker": ("Docker", "infrastructure"),
    "k8s.io/client-go": ("Kubernetes", "infrastructure"),
    "github.com/nats-io/nats.go": ("NATS", "infrastructure"),
    "github.com/rabbitmq/amqp091-go": ("RabbitMQ", "infrastructure"),
    "github.com/prometheus/client_golang": ("Prometheus", "infrastructure"),
    "go.uber.org/zap": ("Zap Logger", "infrastructure"),
    "github.com/sirupsen/logrus": ("Logrus", "infrastructure"),
    "github.com/spf13/cobra": ("Cobra CLI", "infrastructure"),
    "github.com/spf13/viper": ("Viper Config", "infrastructure"),
    # Testing
    "github.com/stretchr/testify": ("Testify", "infrastructure"),
}

RUST_CRATE_MAP = {
    # Web frameworks
    "actix-web": ("Actix Web", "backend"),
    "axum": ("Axum", "backend"),
    "rocket": ("Rocket", "backend"),
    "warp": ("Warp", "backend"),
    "hyper": ("Hyper", "backend"),
    # Async runtime
    "tokio": ("Tokio", "backend"),
    "async-std": ("async-std", "backend"),
    # Serialization
    "serde": ("Serde", "backend"),
    "serde_json": ("Serde JSON", "backend"),
    # Databases
    "diesel": ("Diesel ORM", "database"),
    "sqlx": ("SQLx", "database"),
    "sea-orm": ("SeaORM", "database"),
    "rusqlite": ("SQLite", "database"),
    "redis": ("Redis", "database"),
    "mongodb": ("MongoDB", "database"),
    # AI
    "async-openai": ("OpenAI API", "ai_ml"),
    # Infrastructure
    "aws-sdk-s3": ("AWS SDK", "infrastructure"),
    "tracing": ("Tracing", "infrastructure"),
    "clap": ("Clap CLI", "infrastructure"),
    "tonic": ("gRPC (Tonic)", "backend"),
    "prost": ("Protocol Buffers", "backend"),
    # WebAssembly
    "wasm-bindgen": ("WebAssembly", "frontend"),
    "yew": ("Yew", "frontend"),
    "leptos": ("Leptos", "frontend"),
    "tauri": ("Tauri", "frontend"),
}

RUBY_GEM_MAP = {
    # Web frameworks
    "rails": ("Ruby on Rails", "backend"),
    "sinatra": ("Sinatra", "backend"),
    "hanami": ("Hanami", "backend"),
    "grape": ("Grape API", "backend"),
    # Rails ecosystem
    "devise": ("Devise", "backend"),
    "pundit": ("Pundit", "backend"),
    "sidekiq": ("Sidekiq", "backend"),
    "resque": ("Resque", "backend"),
    "delayed_job": ("Delayed Job", "backend"),
    "activeadmin": ("ActiveAdmin", "backend"),
    # API
    "graphql-ruby": ("GraphQL", "backend"),
    "jbuilder": ("Jbuilder", "backend"),
    # Databases
    "pg": ("PostgreSQL", "database"),
    "mysql2": ("MySQL", "database"),
    "mongoid": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "sequel": ("Sequel", "database"),
    "elasticsearch-model": ("Elasticsearch", "database"),
    # AI
    "ruby-openai": ("OpenAI API", "ai_ml"),
    "langchainrb": ("LangChain (Ruby)", "ai_ml"),
    # Infrastructure
    "puma": ("Puma", "infrastructure"),
    "unicorn": ("Unicorn", "infrastructure"),
    "aws-sdk-s3": ("AWS SDK", "infrastructure"),
    "sentry-ruby": ("Sentry", "infrastructure"),
    "newrelic_rpm": ("New Relic", "infrastructure"),
    # Payments
    "stripe": ("Stripe", "backend"),
    # Testing
    "rspec": ("RSpec", "infrastructure"),
    "capybara": ("Capybara", "infrastructure"),
    "factory_bot": ("FactoryBot", "infrastructure"),
    "faker": ("Faker", "infrastructure"),
}

JAVA_ARTIFACT_MAP = {
    # Spring ecosystem
    "spring-boot-starter-web": ("Spring Boot", "backend"),
    "spring-boot-starter": ("Spring Boot", "backend"),
    "spring-boot-starter-data-jpa": ("Spring Data JPA", "database"),
    "spring-boot-starter-security": ("Spring Security", "backend"),
    "spring-boot-starter-webflux": ("Spring WebFlux", "backend"),
    "spring-cloud-starter": ("Spring Cloud", "backend"),
    # Web
    "jersey-server": ("Jersey", "backend"),
    "dropwizard-core": ("Dropwizard", "backend"),
    "micronaut-http-server": ("Micronaut", "backend"),
    "quarkus-core": ("Quarkus", "backend"),
    "vert.x-core": ("Vert.x", "backend"),
    "vertx-core": ("Vert.x", "backend"),
    # Databases
    "postgresql": ("PostgreSQL", "database"),
    "mysql-connector-java": ("MySQL", "database"),
    "mysql-connector-j": ("MySQL", "database"),
    "mongodb-driver-sync": ("MongoDB", "database"),
    "jedis": ("Redis", "database"),
    "lettuce-core": ("Redis", "database"),
    "hibernate-core": ("Hibernate", "database"),
    "mybatis": ("MyBatis", "database"),
    "flyway-core": ("Flyway", "database"),
    "liquibase-core": ("Liquibase", "database"),
    "elasticsearch-rest-high-level-client": ("Elasticsearch", "database"),
    # Messaging
    "kafka-clients": ("Apache Kafka", "infrastructure"),
    "spring-kafka": ("Apache Kafka", "infrastructure"),
    "amqp-client": ("RabbitMQ", "infrastructure"),
    # AI
    "langchain4j": ("LangChain (Java)", "ai_ml"),
    # gRPC
    "grpc-netty": ("gRPC", "backend"),
    "protobuf-java": ("Protocol Buffers", "backend"),
    # Testing
    "junit-jupiter": ("JUnit 5", "infrastructure"),
    "mockito-core": ("Mockito", "infrastructure"),
    # Infrastructure
    "aws-java-sdk-s3": ("AWS SDK", "infrastructure"),
    "sentry": ("Sentry", "infrastructure"),
    "logback-classic": ("Logback", "infrastructure"),
    "slf4j-api": ("SLF4J", "infrastructure"),
    "micrometer-core": ("Micrometer", "infrastructure"),
}
