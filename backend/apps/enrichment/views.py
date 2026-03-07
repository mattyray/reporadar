from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import APICredential
from apps.enrichment.models import EnrichmentLog, OrganizationContact
from apps.prospects.models import Organization
from providers.hunter import HunterProvider

from .serializers import OrganizationContactSerializer


class EnrichOrganizationView(APIView):
    """POST /api/enrichment/{org_id}/enrich/ — Trigger contact enrichment for an org."""

    def post(self, request, org_id):
        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check for cached results (30-day TTL)
        existing = OrganizationContact.objects.filter(organization=org)
        if existing.exists():
            latest = existing.order_by("-last_enriched_at").first()
            if latest and latest.last_enriched_at:
                days_old = (timezone.now() - latest.last_enriched_at).days
                if days_old < 30:
                    return Response({
                        "cached": True,
                        "contacts": OrganizationContactSerializer(existing, many=True).data,
                    })

        # Get user's Hunter API key
        try:
            cred = APICredential.objects.get(
                user=request.user, provider="hunter", is_valid=True
            )
        except APICredential.DoesNotExist:
            return Response(
                {"detail": "No Hunter.io API key configured. Add one in Settings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        domain = _extract_domain(org)
        if not domain:
            return Response(
                {"detail": "No website domain found for this organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider = HunterProvider()

        # Free check first — does Hunter have any data?
        email_count = provider.email_count(cred.encrypted_key, domain)
        EnrichmentLog.objects.create(
            user=request.user,
            provider="hunter",
            endpoint="email-count",
            domain_searched=domain,
            credits_used=0,
            results_returned=email_count,
            cached=False,
        )

        if email_count == 0:
            return Response({
                "cached": False,
                "contacts": [],
                "message": f"Hunter.io has no email data for {domain}.",
            })

        # Domain search (costs 1 credit)
        result = provider.domain_search(cred.encrypted_key, domain, department="engineering")
        EnrichmentLog.objects.create(
            user=request.user,
            provider="hunter",
            endpoint="domain-search",
            domain_searched=domain,
            credits_used=1,
            results_returned=len(result.contacts),
            cached=False,
        )

        # Save contacts
        contacts = []
        for contact in result.contacts:
            obj, _ = OrganizationContact.objects.update_or_create(
                organization=org,
                email=contact.email,
                defaults={
                    "provider": "hunter",
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "email_confidence": contact.confidence,
                    "position": contact.position,
                    "department": contact.department,
                    "seniority": contact.seniority,
                    "linkedin_url": contact.linkedin_url,
                    "is_engineering_lead": _is_eng_lead(contact.position, contact.seniority),
                    "source_domain": domain,
                    "last_enriched_at": timezone.now(),
                },
            )
            contacts.append(obj)

        return Response({
            "cached": False,
            "contacts": OrganizationContactSerializer(contacts, many=True).data,
        })


class OrganizationContactsView(APIView):
    """GET /api/enrichment/{org_id}/contacts/ — View enriched contacts for an org."""

    def get(self, request, org_id):
        contacts = OrganizationContact.objects.filter(
            organization_id=org_id
        ).order_by("-is_engineering_lead", "-email_confidence")
        return Response(OrganizationContactSerializer(contacts, many=True).data)


def _extract_domain(org):
    """Try to get a domain from the org's website or email."""
    if org.website:
        domain = org.website.replace("https://", "").replace("http://", "").strip("/")
        if "/" in domain:
            domain = domain.split("/")[0]
        return domain
    if org.email and "@" in org.email:
        return org.email.split("@")[1]
    return None


def _is_eng_lead(position, seniority):
    """Determine if this contact is likely an engineering lead."""
    if not position:
        return False
    position_lower = position.lower()
    lead_titles = [
        "vp of engineering", "head of engineering", "engineering manager",
        "director of engineering", "cto", "chief technology",
        "lead engineer", "staff engineer", "principal engineer",
        "engineering lead", "tech lead",
    ]
    return any(title in position_lower for title in lead_titles)
