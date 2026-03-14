import re

from django.db import models
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.enrichment.models import OrganizationContact
from apps.jobs.models import JobListing
from apps.prospects.models import Organization, RepoStackDetection
from apps.resumes.models import ResumeProfile

from .models import OutreachMessage
from .serializers import OutreachGenerateSerializer, OutreachMessageSerializer
from .tasks import generate_outreach_message


class OutreachGenerateView(APIView):
    """POST /api/outreach/generate/ — Generate a personalized outreach message (async)."""

    def post(self, request):
        serializer = OutreachGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            org = Organization.objects.get(pk=serializer.validated_data["organization_id"])
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get user's resume profile
        try:
            resume = ResumeProfile.objects.get(user=request.user)
        except ResumeProfile.DoesNotExist:
            return Response(
                {"detail": "Upload your resume first to generate personalized outreach."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get contact if specified
        contact = None
        contact_id = serializer.validated_data.get("contact_id")
        if contact_id:
            contact = OrganizationContact.objects.filter(pk=contact_id).first()

        # Build context for Claude — aggregate stack across all repos
        org_stack = list(
            RepoStackDetection.objects.filter(
                repo__organization=org
            ).values_list("technology_name", flat=True).distinct()
        )

        # Get open job listings for this company
        open_jobs = list(
            JobListing.objects.filter(
                is_active=True,
            ).filter(
                models.Q(ats_mapping__organization=org) |
                models.Q(company_name__iexact=org.name)
            ).values("title", "department", "location", "detected_techs")[:10]
        )

        context = {
            "organization": {
                "name": org.name,
                "description": org.description,
                "website": org.website,
                "stack": org_stack,
            },
            "contact": {
                "name": f"{contact.first_name} {contact.last_name}" if contact else "",
                "position": contact.position if contact else "",
            },
            "user_profile": {
                "summary": resume.summary,
                "tech_stack": resume.tech_stack,
                "key_projects": resume.key_projects,
                "story_hook": resume.story_hook,
            },
            "open_jobs": open_jobs,
            "message_type": serializer.validated_data["message_type"],
        }

        # Create message in "generating" state, dispatch Celery task
        outreach = OutreachMessage.objects.create(
            user=request.user,
            organization=org,
            contact=contact,
            message_type=serializer.validated_data["message_type"],
            status="generating",
            context_used=context,
        )

        generate_outreach_message.delay(str(outreach.id))

        return Response(
            OutreachMessageSerializer(outreach).data,
            status=status.HTTP_202_ACCEPTED,
        )


class OutreachStatusView(APIView):
    """GET /api/outreach/{id}/status/ — Poll for generation completion."""

    def get(self, request, pk):
        try:
            outreach = OutreachMessage.objects.get(pk=pk, user=request.user)
        except OutreachMessage.DoesNotExist:
            return Response(
                {"detail": "Message not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(OutreachMessageSerializer(outreach).data)


class OutreachHistoryView(generics.ListAPIView):
    """GET /api/outreach/history/ — Past generated messages."""

    serializer_class = OutreachMessageSerializer

    def get_queryset(self):
        return OutreachMessage.objects.filter(user=self.request.user)


def _build_prompt(context):
    msg_type = context["message_type"]
    org = context["organization"]
    contact = context["contact"]
    profile = context["user_profile"]
    open_jobs = context.get("open_jobs", [])

    length_guide = "Keep it under 300 characters." if msg_type == "linkedin_dm" else "Keep it concise — 3-4 short paragraphs max."

    # Format open jobs section
    jobs_section = ""
    if open_jobs:
        job_lines = []
        for j in open_jobs:
            parts = [j.get("title", "")]
            if j.get("department"):
                parts.append(f"({j['department']})")
            if j.get("location"):
                parts.append(f"— {j['location']}")
            techs = j.get("detected_techs") or []
            if techs:
                parts.append(f"[{', '.join(techs[:5])}]")
            job_lines.append("  - " + " ".join(parts))
        jobs_section = f"\n\nOPEN JOBS AT {org.get('name', 'this company').upper()}:\n" + "\n".join(job_lines)

    subject_instruction = ""
    if msg_type == "email":
        subject_instruction = (
            "\n- Start with a subject line on the first line in this exact format: "
            "Subject: Your subject here"
            "\n- Then leave a blank line before the email body."
            "\n- The subject should be specific and reference the role or a shared technology — no generic subjects."
        )
    else:
        subject_instruction = "\n- Do NOT include a subject line."

    return f"""Generate a personalized {msg_type.replace('_', ' ')} from a job seeker to a company.

ABOUT THE SENDER:
- Summary: {profile.get('summary', 'N/A')}
- Tech stack: {', '.join(profile.get('tech_stack', []))}
- Key projects: {profile.get('key_projects', 'N/A')}
- Personal hook: {profile.get('story_hook', 'N/A')}

ABOUT THE COMPANY:
- Name: {org.get('name', 'Unknown')}
- Description: {org.get('description', 'N/A')}
- Their tech stack: {', '.join(org.get('stack', []))}
{jobs_section}

RECIPIENT: {contact.get('name', 'Hiring Manager')} — {contact.get('position', '')}

RULES:
- Reference specific shared technologies between the sender and company
- If the company has open jobs listed above, reference a specific role that matches the sender's background
- Mention a specific project the sender built that's relevant to the company's stack
- Be genuine, not salesy. No buzzwords.
- {length_guide}{subject_instruction}
- Write ONLY the message (and subject line if email). No explanations."""


def _parse_subject(raw_text):
    """Extract subject line from Claude's email response.

    Expected format:
        Subject: Some subject here

        Email body starts here...
    """
    match = re.match(r"^Subject:\s*(.+?)(?:\n\n|\r\n\r\n)(.*)", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    # Fallback: no subject found
    return "", raw_text.strip()
