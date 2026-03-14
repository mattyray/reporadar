from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView


class JobSearchPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500

from apps.prospects.models import Organization

from .models import ATSMapping, JobListing
from .serializers import JobListingSerializer
from .tasks import probe_org_ats


class OrgJobsView(generics.ListAPIView):
    """GET /api/jobs/org/{org_id}/ — List active jobs for a specific organization."""

    serializer_class = JobListingSerializer

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        return (
            JobListing.objects.filter(
                ats_mapping__organization_id=org_id,
                is_active=True,
            )
            .select_related("ats_mapping", "ats_mapping__organization")
            .order_by("-posted_at", "title")
        )


class OrgJobsCheckView(APIView):
    """POST /api/jobs/org/{org_id}/check/ — Trigger ATS probe for an organization."""

    def post(self, request, org_id):
        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if we already have a recent mapping (within 24 hours)
        from django.utils import timezone
        from datetime import timedelta

        recent_cutoff = timezone.now() - timedelta(hours=24)
        has_recent = ATSMapping.objects.filter(
            organization=org,
            last_checked_at__gte=recent_cutoff,
        ).exists()

        if has_recent:
            # Return existing jobs without re-probing
            jobs = JobListing.objects.filter(
                ats_mapping__organization=org,
                is_active=True,
            ).select_related("ats_mapping", "ats_mapping__organization")
            serializer = JobListingSerializer(jobs, many=True)
            return Response({
                "status": "cached",
                "jobs": serializer.data,
            })

        # Queue the probe task
        probe_org_ats.delay(org_id)

        return Response({
            "status": "probing",
            "detail": "Checking ATS platforms for open roles. This may take a few seconds.",
        })


class JobSearchView(generics.ListAPIView):
    """GET /api/jobs/ — Search all active jobs, filterable by tech, location, department."""

    serializer_class = JobListingSerializer
    pagination_class = JobSearchPagination

    def get_queryset(self):
        qs = (
            JobListing.objects.filter(is_active=True)
            .select_related("ats_mapping", "ats_mapping__organization")
            .order_by("-posted_at", "title")
        )

        # Filter by source (e.g. ?source=remoteok or ?source=ats,remoteok)
        source = self.request.query_params.get("source")
        if source:
            source_list = [s.strip() for s in source.split(",") if s.strip()]
            if source_list:
                qs = qs.filter(source__in=source_list)

        # Filter by technologies (match any of the requested techs)
        techs = self.request.query_params.get("techs")
        if techs:
            from django.db.models import Case, IntegerField, Value, When

            from .tech_extraction import TECH_KEYWORDS

            tech_list = [t.strip() for t in techs.split(",") if t.strip()]
            if tech_list:
                # Normalize to canonical names (e.g. "react" → "React")
                canonical_techs = [
                    TECH_KEYWORDS.get(t.lower(), t) for t in tech_list
                ]
                tech_q = Q()
                for canonical in canonical_techs:
                    tech_q |= Q(detected_techs__contains=[canonical])
                qs = qs.filter(tech_q)

                # Sort by relevance: count how many selected techs each job matches
                match_cases = [
                    When(detected_techs__contains=[ct], then=Value(1))
                    for ct in canonical_techs
                ]
                qs = qs.annotate(
                    match_count=sum(
                        Case(mc, default=Value(0), output_field=IntegerField())
                        for mc in match_cases
                    )
                ).order_by("-match_count", "-posted_at", "title")

        # Filter by location keyword
        location = self.request.query_params.get("location")
        if location:
            qs = qs.filter(location__icontains=location)

        # Filter by department keyword
        department = self.request.query_params.get("department")
        if department:
            qs = qs.filter(department__icontains=department)

        # Filter by title keyword
        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        # Filter by recency (e.g. "7" = posted/discovered in the last 7 days)
        days = self.request.query_params.get("days")
        if days:
            try:
                cutoff = timezone.now() - timedelta(days=int(days))
                qs = qs.filter(created_at__gte=cutoff)
            except (ValueError, TypeError):
                pass

        return qs
