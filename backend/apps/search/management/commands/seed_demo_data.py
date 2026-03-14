"""Seed the database with realistic demo data for development and demos."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.prospects.models import (
    Organization,
    OrganizationRepo,
    RepoContributor,
    RepoStackDetection,
)

ORGS = [
    {
        "github_login": "acme-ai",
        "github_id": 100001,
        "name": "Acme AI Labs",
        "description": "Building intelligent automation tools for developers.",
        "website": "https://acmeai.dev",
        "location": "San Francisco, CA",
        "github_url": "https://github.com/acme-ai",
        "public_repos_count": 12,
        "repos": [
            {
                "name": "agent-framework",
                "description": "Production-grade AI agent orchestration framework",
                "stars": 342,
                "forks": 67,
                "stack": [("Django", "backend"), ("Celery", "backend"), ("PostgreSQL", "database"),
                          ("Redis", "infrastructure"), ("React", "frontend"), ("TypeScript", "frontend")],
                "signals": {"claude_md": True, "docker": True, "ci_cd": True, "tests": True, "deploy": True},
            },
            {
                "name": "prompt-studio",
                "description": "Visual prompt engineering and testing platform",
                "stars": 128,
                "forks": 23,
                "stack": [("FastAPI", "backend"), ("Python", "backend"), ("React", "frontend"),
                          ("TypeScript", "frontend"), ("OpenAI", "ai_ml")],
                "signals": {"cursor": True, "docker": True, "ci_cd": True, "tests": True, "deploy": False},
            },
        ],
        "contributors": [
            {"login": "sarahchen", "name": "Sarah Chen", "company": "Acme AI Labs", "contributions": 287},
            {"login": "jmartinez", "name": "Jordan Martinez", "company": "Acme AI Labs", "contributions": 194},
            {"login": "devkumar", "name": "Dev Kumar", "company": "", "contributions": 45},
        ],
        "contacts": [
            {"first_name": "Sarah", "last_name": "Chen", "email": "sarah@acmeai.dev",
             "position": "VP of Engineering", "department": "engineering", "seniority": "executive",
             "confidence": 97, "is_lead": True},
            {"first_name": "Jordan", "last_name": "Martinez", "email": "jordan@acmeai.dev",
             "position": "Staff Engineer", "department": "engineering", "seniority": "senior",
             "confidence": 92, "is_lead": True},
        ],
    },
    {
        "github_login": "stackforge-io",
        "github_id": 100002,
        "name": "StackForge",
        "description": "Open-source developer tools for modern web teams.",
        "website": "https://stackforge.io",
        "location": "Austin, TX",
        "github_url": "https://github.com/stackforge-io",
        "public_repos_count": 8,
        "repos": [
            {
                "name": "deploy-engine",
                "description": "Zero-config deployment platform for Django and Rails apps",
                "stars": 891,
                "forks": 134,
                "stack": [("Django", "backend"), ("Python", "backend"), ("PostgreSQL", "database"),
                          ("Docker", "infrastructure"), ("Terraform", "infrastructure")],
                "signals": {"claude_md": True, "docker": True, "ci_cd": True, "tests": True, "deploy": True},
            },
        ],
        "contributors": [
            {"login": "alexwright", "name": "Alex Wright", "company": "StackForge", "contributions": 523},
            {"login": "priyapatel", "name": "Priya Patel", "company": "StackForge", "contributions": 312},
            {"login": "mikeross", "name": "Mike Ross", "company": "", "contributions": 89},
            {"login": "linakim", "name": "Lina Kim", "company": "StackForge", "contributions": 201},
        ],
        "contacts": [
            {"first_name": "Alex", "last_name": "Wright", "email": "alex@stackforge.io",
             "position": "CTO", "department": "engineering", "seniority": "c_level",
             "confidence": 99, "is_lead": True},
        ],
    },
    {
        "github_login": "neondata",
        "github_id": 100003,
        "name": "NeonData",
        "description": "Real-time analytics infrastructure for SaaS companies.",
        "website": "https://neondata.com",
        "location": "New York, NY",
        "github_url": "https://github.com/neondata",
        "public_repos_count": 15,
        "repos": [
            {
                "name": "pipeline",
                "description": "High-throughput event processing pipeline",
                "stars": 2134,
                "forks": 289,
                "stack": [("Python", "backend"), ("Kafka", "infrastructure"), ("PostgreSQL", "database"),
                          ("Redis", "infrastructure"), ("React", "frontend"), ("TypeScript", "frontend"),
                          ("Grafana", "infrastructure")],
                "signals": {"copilot": True, "docker": True, "ci_cd": True, "tests": True, "deploy": True},
            },
            {
                "name": "dashboard-ui",
                "description": "Embeddable analytics dashboard components",
                "stars": 456,
                "forks": 78,
                "stack": [("React", "frontend"), ("TypeScript", "frontend"), ("D3.js", "frontend"),
                          ("Storybook", "frontend")],
                "signals": {"docker": False, "ci_cd": True, "tests": True, "deploy": False},
            },
        ],
        "contributors": [
            {"login": "emilyz", "name": "Emily Zhang", "company": "NeonData", "contributions": 678},
            {"login": "carlosm", "name": "Carlos Mendez", "company": "NeonData", "contributions": 445},
            {"login": "rebeccal", "name": "Rebecca Liu", "company": "NeonData", "contributions": 312},
        ],
        "contacts": [
            {"first_name": "Emily", "last_name": "Zhang", "email": "emily@neondata.com",
             "position": "Head of Engineering", "department": "engineering", "seniority": "executive",
             "confidence": 95, "is_lead": True},
            {"first_name": "Carlos", "last_name": "Mendez", "email": "carlos@neondata.com",
             "position": "Senior Engineer", "department": "engineering", "seniority": "senior",
             "confidence": 88, "is_lead": False},
        ],
    },
    {
        "github_login": "buildkit-labs",
        "github_id": 100004,
        "name": "BuildKit Labs",
        "description": "CI/CD tooling and build optimization for monorepos.",
        "website": "https://buildkit.dev",
        "location": "Remote",
        "github_url": "https://github.com/buildkit-labs",
        "public_repos_count": 6,
        "repos": [
            {
                "name": "turbo-ci",
                "description": "Intelligent CI pipeline that only runs affected tests",
                "stars": 567,
                "forks": 43,
                "stack": [("Python", "backend"), ("Django", "backend"), ("Celery", "backend"),
                          ("React", "frontend"), ("TypeScript", "frontend"), ("LangChain", "ai_ml")],
                "signals": {"claude_md": True, "windsurf": True, "docker": True, "ci_cd": True, "tests": True, "deploy": True},
            },
        ],
        "contributors": [
            {"login": "natashak", "name": "Natasha Kowalski", "company": "BuildKit Labs", "contributions": 234},
            {"login": "ryanf", "name": "Ryan Foster", "company": "BuildKit Labs", "contributions": 189},
        ],
        "contacts": [
            {"first_name": "Natasha", "last_name": "Kowalski", "email": "natasha@buildkit.dev",
             "position": "Engineering Lead", "department": "engineering", "seniority": "senior",
             "confidence": 91, "is_lead": True},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with realistic demo organizations, repos, and contacts."

    def handle(self, *args, **options):
        now = timezone.now()
        created_orgs = 0

        for org_data in ORGS:
            org, created = Organization.objects.update_or_create(
                github_id=org_data["github_id"],
                defaults={
                    "github_login": org_data["github_login"],
                    "name": org_data["name"],
                    "description": org_data["description"],
                    "website": org_data["website"],
                    "location": org_data["location"],
                    "github_url": org_data["github_url"],
                    "public_repos_count": org_data["public_repos_count"],
                    "avatar_url": f"https://ui-avatars.com/api/?name={org_data['name'].replace(' ', '+')}&size=128&background=random",
                    "last_scanned_at": now,
                },
            )
            if created:
                created_orgs += 1

            for i, repo_data in enumerate(org_data["repos"]):
                repo, _ = OrganizationRepo.objects.update_or_create(
                    github_id=org_data["github_id"] * 100 + i,
                    defaults={
                        "organization": org,
                        "name": repo_data["name"],
                        "full_name": f"{org_data['github_login']}/{repo_data['name']}",
                        "description": repo_data["description"],
                        "url": f"https://github.com/{org_data['github_login']}/{repo_data['name']}",
                        "stars": repo_data["stars"],
                        "forks": repo_data["forks"],
                        "has_claude_md": repo_data["signals"].get("claude_md", False),
                        "has_cursor_config": repo_data["signals"].get("cursor", False),
                        "has_copilot_config": repo_data["signals"].get("copilot", False),
                        "has_windsurf_config": repo_data["signals"].get("windsurf", False),
                        "has_docker": repo_data["signals"].get("docker", False),
                        "has_ci_cd": repo_data["signals"].get("ci_cd", False),
                        "has_tests": repo_data["signals"].get("tests", False),
                        "has_deployment_config": repo_data["signals"].get("deploy", False),
                        "last_pushed_at": now - timedelta(days=3),
                        "last_scanned_at": now,
                    },
                )

                for tech_name, category in repo_data["stack"]:
                    RepoStackDetection.objects.update_or_create(
                        repo=repo,
                        technology_name=tech_name,
                        defaults={"category": category, "source_file": "detected"},
                    )

            for j, contrib in enumerate(org_data.get("contributors", [])):
                first_repo = org.repos.first()
                if first_repo:
                    RepoContributor.objects.update_or_create(
                        repo=first_repo,
                        github_id=org_data["github_id"] * 1000 + j,
                        defaults={
                            "github_username": contrib["login"],
                            "name": contrib["name"],
                            "company": contrib["company"],
                            "avatar_url": f"https://ui-avatars.com/api/?name={contrib['name'].replace(' ', '+')}&size=64",
                            "contributions": contrib["contributions"],
                            "profile_url": f"https://github.com/{contrib['login']}",
                            "last_fetched_at": now,
                        },
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(ORGS)} organizations ({created_orgs} new) with repos and contributors."
        ))
