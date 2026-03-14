"""Extract technology names from job description text.

Reuses the known tech names from search/detection.py but matches them
as keywords in free text rather than parsing dependency files.
"""

import re

# All known tech names we want to detect in job descriptions.
# Maps lowercase search term → canonical display name.
TECH_KEYWORDS = {
    # Python ecosystem
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "celery": "Celery",
    "django rest framework": "Django REST Framework",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    # JavaScript/TypeScript ecosystem
    "react": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "svelte": "Svelte",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "nestjs": "NestJS",
    "hono": "Hono",
    "remix": "Remix",
    "astro": "Astro",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "trpc": "tRPC",
    "socket.io": "Socket.IO",
    # Auth
    "auth0": "Auth0",
    "clerk": "Clerk",
    "nextauth": "NextAuth.js",
    "firebase": "Firebase",
    "supabase": "Supabase",
    "keycloak": "Keycloak",
    # Payments
    "stripe": "Stripe",
    "paddle": "Paddle",
    # Databases
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "sqlite": "SQLite",
    "cassandra": "Cassandra",
    "neo4j": "Neo4j",
    "clickhouse": "ClickHouse",
    "prisma": "Prisma",
    "drizzle": "Drizzle ORM",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "neon": "Neon",
    "planetscale": "PlanetScale",
    # AI/ML
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "llamaindex": "LlamaIndex",
    "llama index": "LlamaIndex",
    "openai": "OpenAI",
    "gpt-4": "OpenAI",
    "gpt-3": "OpenAI",
    "chatgpt": "OpenAI",
    "claude": "Claude",
    "anthropic": "Claude",
    "claude api": "Claude",
    "gemini": "Google Gemini",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "hugging face": "Hugging Face",
    "scikit-learn": "scikit-learn",
    "machine learning": "Machine Learning",
    "llm": "LLM",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    # Vector databases
    "pinecone": "Pinecone",
    "chromadb": "ChromaDB",
    "chroma": "ChromaDB",
    "weaviate": "Weaviate",
    "qdrant": "Qdrant",
    "pgvector": "pgvector",
    "faiss": "FAISS",
    # AI tools/frameworks
    "crewai": "CrewAI",
    "autogen": "AutoGen",
    "dspy": "DSPy",
    "vllm": "vLLM",
    "ollama": "Ollama",
    "litellm": "LiteLLM",
    "vercel ai": "Vercel AI SDK",
    "mlflow": "MLflow",
    "weights & biases": "Weights & Biases",
    "wandb": "Weights & Biases",
    # Infrastructure
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "azure": "Azure",
    "terraform": "Terraform",
    "pulumi": "Pulumi",
    "cloudflare workers": "Cloudflare Workers",
    "serverless": "Serverless",
    "aws lambda": "AWS Lambda",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "datadog": "Datadog",
    "sentry": "Sentry",
    "new relic": "New Relic",
    "opentelemetry": "OpenTelemetry",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    # Other
    "graphql": "GraphQL",
    "rest api": "REST API",
    "restful": "REST API",
    "grpc": "gRPC",
    "rabbitmq": "RabbitMQ",
    "kafka": "Kafka",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    "python": "Python",
    "java": "Java",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "php": "PHP",
    "laravel": "Laravel",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "c#": "C#",
    ".net": ".NET",
    "elixir": "Elixir",
    "scala": "Scala",
}

# Pre-compile patterns for efficiency — sort by length descending so longer
# matches take priority (e.g. "next.js" before "next", "ruby on rails" before "ruby")
_PATTERNS = []
for keyword in sorted(TECH_KEYWORDS.keys(), key=len, reverse=True):
    escaped = re.escape(keyword)
    # Word boundary matching, case insensitive
    pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    _PATTERNS.append((pattern, TECH_KEYWORDS[keyword]))


def extract_techs_from_text(text: str) -> list[str]:
    """Extract known technology names from free text (job descriptions, etc.).

    Returns a deduplicated list of canonical tech names found in the text.
    """
    if not text:
        return []

    found = set()
    for pattern, canonical_name in _PATTERNS:
        if pattern.search(text):
            found.add(canonical_name)

    return sorted(found)
