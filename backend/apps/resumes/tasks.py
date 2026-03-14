"""Celery task for parsing resumes with Claude API."""

import json
import os

import anthropic
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=2)
def parse_resume(self, profile_id: int):
    """Extract structured data from an uploaded resume using Claude API."""
    from .models import ResumeProfile

    profile = ResumeProfile.objects.get(pk=profile_id)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    # Read the uploaded file
    raw_text = _extract_text(profile)
    if not raw_text:
        raise RuntimeError("Could not extract text from resume")

    # Send to Claude for structured extraction
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": _build_parse_prompt(raw_text),
            }
        ],
    )

    try:
        parsed = json.loads(message.content[0].text)
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError("Claude returned invalid JSON for resume parsing")

    # Update the profile with parsed data
    profile.parsed_data = parsed
    profile.summary = parsed.get("summary", "")
    profile.key_projects = parsed.get("key_projects", [])
    # Normalize tech names to match job detection canonical names
    from apps.jobs.tech_extraction import TECH_KEYWORDS

    raw_techs = parsed.get("tech_stack", [])
    normalized_techs = []
    seen = set()
    for t in raw_techs:
        tl = t.lower()
        canonical = TECH_KEYWORDS.get(tl)
        if not canonical:
            for kw, cn in TECH_KEYWORDS.items():
                if kw in tl or tl in kw:
                    canonical = cn
                    break
        final = canonical or t
        if final not in seen:
            normalized_techs.append(final)
            seen.add(final)
    profile.tech_stack = normalized_techs
    profile.years_experience = parsed.get("years_experience")
    profile.story_hook = parsed.get("story_hook", "")
    profile.parsed_at = timezone.now()
    profile.save(update_fields=[
        "parsed_data", "summary", "key_projects", "tech_stack",
        "years_experience", "story_hook", "parsed_at",
    ])

    # Auto-match jobs against the parsed tech stack
    from .matching import match_jobs_for_user

    match_count = match_jobs_for_user(profile.user_id)

    return {"status": "parsed", "profile_id": profile_id, "matched_jobs": match_count}


@shared_task
def refresh_all_job_matches():
    """Re-match all users with resume profiles against current jobs.

    Run daily via Celery Beat to pick up new job listings.
    """
    from .matching import match_jobs_for_user
    from .models import ResumeProfile

    user_ids = list(
        ResumeProfile.objects.filter(parsed_at__isnull=False)
        .values_list("user_id", flat=True)
    )

    total_matches = 0
    for user_id in user_ids:
        total_matches += match_jobs_for_user(user_id)

    return {"users_processed": len(user_ids), "total_matches": total_matches}


def _extract_text(profile):
    """Extract plain text from PDF or DOCX resume."""
    file_path = profile.original_file.path

    if profile.file_type == "pdf":
        return _extract_pdf_text(file_path)
    elif profile.file_type == "docx":
        return _extract_docx_text(file_path)
    return None


def _extract_pdf_text(file_path):
    """Extract text from a PDF file using pdfminer."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        if text and text.strip():
            return text
        return None
    except ImportError:
        raise RuntimeError(
            "pdfminer.six is not installed. Cannot extract text from PDF. "
            "Run: pip install pdfminer.six"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


def _extract_docx_text(file_path):
    """Extract text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        if text and text.strip():
            return text
        return None
    except ImportError:
        raise RuntimeError(
            "python-docx is not installed. Cannot extract text from DOCX. "
            "Run: pip install python-docx"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from DOCX: {e}")


def _build_parse_prompt(resume_text):
    return f"""Parse this resume and extract structured data. Return ONLY valid JSON with these fields:

{{
  "summary": "2-3 sentence professional summary",
  "tech_stack": ["list", "of", "technologies"],
  "key_projects": [
    {{"name": "Project Name", "description": "What it does", "tech": ["tech1", "tech2"]}}
  ],
  "years_experience": 5,
  "story_hook": "A unique personal angle or narrative hook for outreach messages"
}}

RULES:
- tech_stack should be specific: "Django" not "Python web frameworks"
- key_projects: pick the 3-5 most impressive/relevant projects
- story_hook: what makes this person's background unique or interesting? Something a recruiter would remember.
- years_experience: best estimate as an integer, null if unclear
- Return ONLY the JSON object, no markdown code fences, no explanation

RESUME TEXT:
{resume_text}"""
