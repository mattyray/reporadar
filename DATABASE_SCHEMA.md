# RepoRadar — Database Schema

## Models Overview

```
User (Django auth)
 ├── APICredential (encrypted keys for GitHub, Hunter, Apollo)
 ├── SearchQuery (saved searches with config)
 │    └── SearchResult (links search → prospects found)
 ├── SavedProspect (user's bookmarked prospects)
 ├── ResumeProfile (parsed resume data)
 └── OutreachMessage (generated messages)

Organization (GitHub org — shared across users)
 ├── OrganizationRepo (repos belonging to org)
 │    ├── RepoStackDetection (detected technologies)
 │    └── RepoContributor (GitHub contributor profiles)
 └── OrganizationContact (enriched contacts from Hunter/Apollo)
```

---

## accounts app

### User
Django's built-in User model, extended via django-allauth for OAuth. django-allauth stores social account data (Google, GitHub) in its own tables (`socialaccount_socialaccount`, `socialaccount_socialtoken`).

The GitHub OAuth token stored by allauth IS the GitHub API credential — no separate storage needed.

### APICredential
Stores user's manually-entered API keys for Hunter.io and Apollo.io (BYOK). GitHub tokens are handled by django-allauth's SocialToken model instead.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| user | FK → User | ON DELETE CASCADE |
| provider | CharField(20) | choices: `hunter`, `apollo` |
| encrypted_key | EncryptedCharField(500) | Fernet encryption via django-fernet-encrypted-fields |
| is_valid | BooleanField | Default True, set False on auth failure |
| credits_remaining | IntegerField | Nullable, last known balance |
| credits_checked_at | DateTimeField | Nullable, when we last checked balance |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Constraints:** unique_together = (user, provider)

**Helper method on User model or manager:**
```python
def get_github_token(user):
    """Get GitHub OAuth token from allauth's SocialToken."""
    from allauth.socialaccount.models import SocialToken
    token = SocialToken.objects.filter(
        account__user=user,
        account__provider='github'
    ).first()
    return token.token if token else None

def has_github_connected(user):
    """Check if user has connected their GitHub account."""
    from allauth.socialaccount.models import SocialAccount
    return SocialAccount.objects.filter(
        user=user, provider='github'
    ).exists()
```

---

## search app

### SearchQuery
A search configuration + execution record.

| Field | Type | Notes |
|-------|------|-------|
| id | UUIDField | PK, default uuid4 |
| user | FK → User | ON DELETE CASCADE |
| name | CharField(200) | Optional friendly name |
| config | JSONField | Full search config (see CLAUDE.md schema) |
| status | CharField(20) | choices: `pending`, `running`, `completed`, `failed` |
| total_repos_found | IntegerField | Default 0 |
| total_orgs_found | IntegerField | Default 0 |
| error_message | TextField | Blank, for failed searches |
| celery_task_id | CharField(255) | Blank, for job tracking |
| started_at | DateTimeField | Nullable |
| completed_at | DateTimeField | Nullable |
| created_at | DateTimeField | auto_now_add |

### SearchPreset
Saved search configurations for reuse.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| user | FK → User | ON DELETE CASCADE |
| name | CharField(200) | Required |
| config | JSONField | Search config without execution state |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

---

## prospects app

### Organization
A GitHub organization. Shared across all users (not per-user).

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| github_login | CharField(100) | Unique, the org's GitHub username |
| github_id | IntegerField | Unique, GitHub's numeric ID |
| name | CharField(200) | Display name from GitHub |
| description | TextField | Blank |
| website | URLField | Blank, from GitHub profile |
| email | EmailField | Blank, from GitHub profile |
| location | CharField(200) | Blank |
| blog | URLField | Blank |
| avatar_url | URLField | Blank |
| public_repos_count | IntegerField | Default 0 |
| github_url | URLField | `https://github.com/{login}` |
| careers_url | URLField | Blank, guessed or manually set |
| linkedin_search_url | URLField | Blank, auto-generated |
| last_scanned_at | DateTimeField | Nullable, when we last fetched from GitHub |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Index:** github_login, github_id

### OrganizationRepo
A repo belonging to an org that matched a search.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| organization | FK → Organization | ON DELETE CASCADE |
| github_id | IntegerField | Unique |
| name | CharField(200) | |
| full_name | CharField(400) | `org/repo` |
| description | TextField | Blank |
| url | URLField | GitHub URL |
| stars | IntegerField | Default 0 |
| forks | IntegerField | Default 0 |
| is_fork | BooleanField | Default False |
| default_branch | CharField(100) | Default 'main' |
| languages | JSONField | `{"Python": 45000, "TypeScript": 32000}` |
| has_claude_md | BooleanField | Default False |
| has_cursor_config | BooleanField | Default False |
| has_copilot_config | BooleanField | Default False |
| has_docker | BooleanField | Default False |
| has_ci_cd | BooleanField | Default False |
| has_tests | BooleanField | Default False |
| has_deployment_config | BooleanField | Default False |
| last_pushed_at | DateTimeField | Nullable |
| created_at_github | DateTimeField | Nullable |
| last_scanned_at | DateTimeField | Nullable |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Index:** organization, github_id, full_name

### RepoStackDetection
Technologies detected in a repo from dependency files.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| repo | FK → OrganizationRepo | ON DELETE CASCADE |
| technology_name | CharField(100) | e.g. "Django", "LangGraph", "React" |
| category | CharField(50) | choices: `backend`, `frontend`, `ai_ml`, `database`, `infrastructure`, `ai_tool` |
| source_file | CharField(200) | e.g. "requirements.txt", "package.json" |
| detected_at | DateTimeField | auto_now_add |

**Constraint:** unique_together = (repo, technology_name)

### RepoContributor
GitHub contributor linked to a repo.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| repo | FK → OrganizationRepo | ON DELETE CASCADE |
| github_username | CharField(100) | |
| github_id | IntegerField | |
| name | CharField(200) | Blank, from user profile |
| email | EmailField | Blank, public email from GitHub |
| company | CharField(200) | Blank, from GitHub profile |
| bio | TextField | Blank |
| location | CharField(200) | Blank |
| blog | URLField | Blank |
| twitter_username | CharField(100) | Blank |
| avatar_url | URLField | Blank |
| contributions | IntegerField | Default 0 |
| profile_url | URLField | `https://github.com/{username}` |
| last_fetched_at | DateTimeField | Nullable |
| created_at | DateTimeField | auto_now_add |

**Index:** github_username, repo

### SearchResult
Links a SearchQuery to the Organizations it found.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| search | FK → SearchQuery | ON DELETE CASCADE |
| organization | FK → Organization | ON DELETE CASCADE |
| repo | FK → OrganizationRepo | ON DELETE CASCADE |
| match_score | IntegerField | 0-100 |
| matched_stack | JSONField | `["Django", "LangGraph", "Claude Code"]` |
| created_at | DateTimeField | auto_now_add |

**Constraint:** unique_together = (search, repo)
**Ordering:** -match_score

### SavedProspect
User's bookmarked organizations.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| user | FK → User | ON DELETE CASCADE |
| organization | FK → Organization | ON DELETE CASCADE |
| notes | TextField | Blank, user's private notes |
| status | CharField(20) | choices: `new`, `researched`, `contacted`, `interviewing`, `passed` |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**Constraint:** unique_together = (user, organization)

---

## enrichment app

### OrganizationContact
Enriched contact from Hunter.io or Apollo.io. Shared across users.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| organization | FK → Organization | ON DELETE CASCADE |
| provider | CharField(20) | choices: `hunter`, `apollo`, `github` |
| first_name | CharField(100) | Blank |
| last_name | CharField(100) | Blank |
| email | EmailField | |
| email_confidence | IntegerField | 0-100, from provider |
| email_verified | BooleanField | Default False |
| position | CharField(200) | Blank, job title |
| department | CharField(100) | Blank: `executive`, `engineering`, `it`, etc. |
| seniority | CharField(50) | Blank: `junior`, `senior`, `executive` |
| linkedin_url | URLField | Blank |
| twitter_url | URLField | Blank |
| phone | CharField(50) | Blank |
| is_engineering_lead | BooleanField | Default False, computed from title/dept |
| source_domain | CharField(200) | The domain searched |
| last_enriched_at | DateTimeField | Nullable |
| created_at | DateTimeField | auto_now_add |

**Index:** organization, email, is_engineering_lead

### EnrichmentLog
Tracks API calls for credit awareness.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| user | FK → User | ON DELETE CASCADE |
| provider | CharField(20) | `hunter`, `apollo` |
| endpoint | CharField(100) | e.g. `domain-search`, `email-finder` |
| domain_searched | CharField(200) | |
| credits_used | DecimalField(5,1) | e.g. 1.0, 0.5 |
| results_returned | IntegerField | Default 0 |
| cached | BooleanField | Default False, was this served from cache |
| created_at | DateTimeField | auto_now_add |

---

## resumes app

### ResumeProfile
Parsed resume data for outreach personalization.

| Field | Type | Notes |
|-------|------|-------|
| id | BigAutoField | PK |
| user | OneToOneField → User | ON DELETE CASCADE |
| original_file | FileField | Upload path: `resumes/{user_id}/` |
| file_type | CharField(10) | `pdf`, `docx` |
| parsed_data | JSONField | Structured output from Claude (see below) |
| summary | TextField | Blank, one-paragraph summary |
| key_projects | JSONField | `[{"name": "ToteTaxi", "stack": [...], "highlights": [...]}]` |
| tech_stack | JSONField | `["Django", "React", "LangGraph", ...]` |
| years_experience | IntegerField | Nullable |
| story_hook | TextField | Blank, the personal differentiator |
| parsed_at | DateTimeField | Nullable |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

**parsed_data JSON structure:**
```json
{
  "name": "Matt Raynor",
  "title": "AI/ML Engineer",
  "location": "Hampton Bays, NY",
  "summary": "...",
  "projects": [
    {
      "name": "ToteTaxi",
      "url": "totetaxi.com",
      "stack": ["Django", "React", "LangGraph", "Claude API"],
      "highlights": [
        "LangGraph ReAct agent with 6 tools hitting live DB",
        "310+ tests",
        "22-parameter booking handoff"
      ]
    }
  ],
  "tech_stack": {
    "backend": ["Python", "Django", "DRF"],
    "frontend": ["React", "TypeScript", "Next.js"],
    "ai_ml": ["LangGraph", "LangChain", "Claude API"],
    "infrastructure": ["AWS", "Docker", "Railway"]
  },
  "years_experience": 3,
  "story_hook": "Career-ending diving accident → self-taught engineer → 4 production apps live",
  "strongest_talking_points": [
    "310+ tests with separated business logic from LLM orchestration",
    "Security audit: IDOR vulnerability mitigation",
    "Production LangGraph agent with live DB tools"
  ]
}
```

---

## outreach app

### OutreachMessage
AI-generated personalized outreach messages.

| Field | Type | Notes |
|-------|------|-------|
| id | UUIDField | PK, default uuid4 |
| user | FK → User | ON DELETE CASCADE |
| organization | FK → Organization | ON DELETE CASCADE |
| contact | FK → OrganizationContact | Nullable, ON DELETE SET NULL |
| message_type | CharField(20) | choices: `linkedin_dm`, `email`, `other` |
| subject | CharField(200) | Blank, for emails |
| body | TextField | The generated message |
| context_used | JSONField | What data was fed to Claude for generation |
| created_at | DateTimeField | auto_now_add |

---

## Provider Adapter Interface

```python
# providers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ContactResult:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    confidence: int = 0
    verified: bool = False
    position: str = ""
    department: str = ""
    seniority: str = ""
    linkedin_url: str = ""

@dataclass
class DomainInfo:
    domain: str
    organization: str = ""
    total_emails: int = 0
    personal_emails: int = 0
    contacts: list[ContactResult] = None

class EnrichmentProvider(ABC):
    """Base class for contact enrichment providers."""

    @abstractmethod
    def check_credits(self, api_key: str) -> dict:
        """Return remaining credits info. Should be free/no-cost call."""
        pass

    @abstractmethod
    def email_count(self, api_key: str, domain: str) -> int:
        """Return count of emails available for domain. Should be free/no-cost."""
        pass

    @abstractmethod
    def domain_search(self, api_key: str, domain: str, department: str = None) -> DomainInfo:
        """Search for contacts at a domain. Costs credits."""
        pass

    @abstractmethod
    def find_email(self, api_key: str, domain: str, first_name: str, last_name: str) -> ContactResult:
        """Find specific person's email. Costs credits."""
        pass
```

---

## Migration Strategy

Build models in this order (each depends on the previous):
1. `accounts` — User is Django built-in, add APICredential
2. `prospects` — Organization, OrganizationRepo, RepoStackDetection, RepoContributor
3. `search` — SearchQuery, SearchPreset, SearchResult (depends on prospects)
4. `enrichment` — OrganizationContact, EnrichmentLog (depends on prospects)
5. `resumes` — ResumeProfile (depends on accounts only)
6. `outreach` — OutreachMessage (depends on prospects, enrichment, accounts)
