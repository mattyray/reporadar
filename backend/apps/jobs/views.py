from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

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

    def get_queryset(self):
        qs = (
            JobListing.objects.filter(is_active=True)
            .select_related("ats_mapping", "ats_mapping__organization")
            .order_by("-posted_at", "title")
        )

        # Filter by technologies (match any of the requested techs)
        techs = self.request.query_params.get("techs")
        if techs:
            tech_list = [t.strip() for t in techs.split(",") if t.strip()]
            if tech_list:
                # Filter jobs where detected_techs contains any of the requested techs
                tech_q = Q()
                for tech in tech_list:
                    tech_q |= Q(detected_techs__contains=tech)
                qs = qs.filter(tech_q)

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

        return qs
