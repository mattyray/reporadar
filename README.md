# RepoRadar

Find companies building with your tech stack. Search GitHub organizations by technology, detect AI development tools (Claude Code, Cursor, Copilot), enrich with business contact data, and generate personalized outreach.

## What It Does

1. **Search** — Scan GitHub for organization-owned repos matching your stack criteria (Django + LangGraph, MERN + Copilot, whatever)
2. **Detect** — Analyze dependency files, infrastructure configs, and AI tool signals to identify what companies actually build with
3. **Score** — Rank prospects by stack match, production signals, activity, and team size
4. **Enrich** — Pull business emails and hiring manager contacts via Hunter.io (BYOK)
5. **Outreach** — Upload your resume and generate personalized messages that reference shared stack and specific projects

## Tech Stack

- **Backend:** Django 5, DRF, Celery, Redis, PostgreSQL
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS
- **AI:** Claude API (resume parsing, outreach generation)
- **External APIs:** GitHub REST API, Hunter.io, Apollo.io (optional)

## Quick Start

```bash
# Clone
git clone https://github.com/mattyray/reporadar.git
cd reporadar

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your values
python manage.py migrate
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Services (separate terminal)
docker-compose up redis
celery -A config worker -l info
```

## Authentication

**Sign up** with Google (one click, everyone has a Google account).

**Connect GitHub** in settings to enable search. This uses GitHub OAuth — click a button, approve on GitHub, done. Your GitHub token gives the app read-only access to public repos and orgs.

**Add Hunter.io / Apollo.io keys** in settings for contact enrichment. These are manual API key entry since those services don't support third-party OAuth.

Your credentials are encrypted before storage and never shared between users.

## Build Phases

### Phase 1: Core Search (MVP)
GitHub search + stack detection + org filtering + contributor info + scoring

### Phase 2: Contact Enrichment
Hunter.io integration + Apollo adapter + credit tracking + caching

### Phase 3: Resume + AI Outreach
Resume upload/parsing + personalized message generation via Claude

### Phase 4: Polish + Scale
Stripe billing, shared credentials option, GitHub App registration, export features

## Docs

- [CLAUDE.md](CLAUDE.md) — Full project context for Claude Code
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) — Complete data model specification
- [SKILLS.md](SKILLS.md) — Technical skills demonstrated (for resume/portfolio/interviews)
- [BUILD_LOG.md](BUILD_LOG.md) — Architecture decisions, learnings, war stories (for LinkedIn/Substack content)
