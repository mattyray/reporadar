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
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    # Databases
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "sqlite": "SQLite",
    # AI/ML
    "langchain": "LangChain",
    "openai": "OpenAI",
    "claude": "Claude",
    "anthropic": "Claude",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "hugging face": "Hugging Face",
    "scikit-learn": "scikit-learn",
    "machine learning": "Machine Learning",
    "llm": "LLM",
    # Infrastructure
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "azure": "Azure",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    # Other
    "graphql": "GraphQL",
    "rest api": "REST API",
    "restful": "REST API",
    "grpc": "gRPC",
    "rabbitmq": "RabbitMQ",
    "kafka": "Kafka",
    "prisma": "Prisma",
    "drizzle": "Drizzle ORM",
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
