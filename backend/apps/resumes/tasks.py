"""Celery task for parsing resumes with Claude API."""

import os

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
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": _build_parse_prompt(raw_text),
            }
        ],
    )

    import json

    try:
        parsed = json.loads(message.content[0].text)
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError("Claude returned invalid JSON for resume parsing")

    # Update the profile with parsed data
    profile.parsed_data = parsed
    profile.summary = parsed.get("summary", "")
    profile.key_projects = parsed.get("key_projects", [])
    profile.tech_stack = parsed.get("tech_stack", [])
    profile.years_experience = parsed.get("years_experience")
    profile.story_hook = parsed.get("story_hook", "")
    profile.parsed_at = timezone.now()
    profile.save(update_fields=[
        "parsed_data", "summary", "key_projects", "tech_stack",
        "years_experience", "story_hook", "parsed_at",
    ])

    return {"status": "parsed", "profile_id": profile_id}


def _extract_text(profile):
    """Extract plain text from PDF or DOCX resume."""
    file_path = profile.original_file.path

    if profile.file_type == "pdf":
        return _extract_pdf_text(file_path)
    elif profile.file_type == "docx":
        return _extract_docx_text(file_path)
    return None


def _extract_pdf_text(file_path):
    """Extract text from a PDF file. Tries pdfminer, falls back to reading raw."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(file_path)
    except ImportError:
        # Fallback: read raw bytes and send to Claude as-is
        with open(file_path, "rb") as f:
            return f"[PDF binary, {len(f.read())} bytes — could not extract text. Install pdfminer.six.]"


def _extract_docx_text(file_path):
    """Extract text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        return None


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
