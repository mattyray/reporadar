import os

import anthropic
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.enrichment.models import OrganizationContact
from apps.prospects.models import Organization, RepoStackDetection
from apps.resumes.models import ResumeProfile

from .models import OutreachMessage
from .serializers import OutreachGenerateSerializer, OutreachMessageSerializer


class OutreachGenerateView(APIView):
    """POST /api/outreach/generate/ — Generate a personalized outreach message."""

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
            "message_type": serializer.validated_data["message_type"],
        }

        # Generate with Claude API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return Response(
                {"detail": "Anthropic API key not configured on server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": _build_prompt(context),
                    }
                ],
            )
            body = message.content[0].text
        except Exception as e:
            return Response(
                {"detail": f"AI generation failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Save the generated message
        outreach = OutreachMessage.objects.create(
            user=request.user,
            organization=org,
            contact=contact,
            message_type=serializer.validated_data["message_type"],
            body=body,
            context_used=context,
        )

        return Response(
            OutreachMessageSerializer(outreach).data,
            status=status.HTTP_201_CREATED,
        )


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

    length_guide = "Keep it under 300 characters." if msg_type == "linkedin_dm" else "Keep it concise — 3-4 short paragraphs max."

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

RECIPIENT: {contact.get('name', 'Hiring Manager')} — {contact.get('position', '')}

RULES:
- Reference specific shared technologies between the sender and company
- Mention a specific project the sender built that's relevant to the company's stack
- Be genuine, not salesy. No buzzwords.
- {length_guide}
- Do NOT include a subject line unless this is an email.
- Write ONLY the message body."""
