import csv

from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, OrganizationRepo, SavedProspect
from .serializers import (
    OrganizationDetailSerializer,
    OrganizationListSerializer,
    OrganizationRepoSerializer,
    SavedProspectSerializer,
)


class ProspectListView(generics.ListAPIView):
    """GET /api/prospects/ — List organizations discovered by the current user's searches."""

    serializer_class = OrganizationListSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            search_results__search__user=self.request.user
        ).distinct().order_by("-updated_at")


class ProspectDetailView(generics.RetrieveAPIView):
    """GET /api/prospects/{id}/ — Organization detail with repos and contributors."""

    serializer_class = OrganizationDetailSerializer
    queryset = Organization.objects.all().prefetch_related(
        "repos__stack_detections", "repos__contributors"
    )


class SaveProspectView(APIView):
    """POST /api/prospects/{id}/save/ — Save org to user's prospect list."""

    def post(self, request, pk):
        try:
            org = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        saved, created = SavedProspect.objects.get_or_create(
            user=request.user,
            organization=org,
            defaults={"notes": request.data.get("notes", "")},
        )

        if not created:
            return Response(
                {"detail": "Already saved."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            SavedProspectSerializer(saved).data,
            status=status.HTTP_201_CREATED,
        )


class SavedProspectListView(generics.ListAPIView):
    """GET /api/prospects/saved/ — User's saved prospects."""

    serializer_class = SavedProspectSerializer

    def get_queryset(self):
        return SavedProspect.objects.filter(
            user=self.request.user
        ).select_related("organization")


class SavedProspectDeleteView(generics.DestroyAPIView):
    """DELETE /api/prospects/saved/{id}/ — Remove from saved. Scoped to current user."""

    def get_queryset(self):
        return SavedProspect.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own saved prospects.")
        super().perform_destroy(instance)


class RepoAnalyzeView(APIView):
    """POST /api/prospects/repos/{repo_id}/analyze/ — Trigger AI analysis for a repo."""

    def post(self, request, repo_id):
        from django.utils import timezone as tz
        from datetime import timedelta

        try:
            repo = OrganizationRepo.objects.get(pk=repo_id)
        except OrganizationRepo.DoesNotExist:
            return Response(
                {"detail": "Repository not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Don't re-analyze if already in progress (unless stuck > 5 min)
        if repo.ai_analysis_status in ("analyzing", "pending"):
            stale_cutoff = tz.now() - timedelta(minutes=5)
            if repo.updated_at > stale_cutoff:
                return Response(
                    {"detail": "Analysis already in progress.", "status": repo.ai_analysis_status},
                    status=status.HTTP_409_CONFLICT,
                )

        # Mark as pending and kick off the task
        repo.ai_analysis_status = "pending"
        repo.ai_analysis_error = ""
        repo.save(update_fields=["ai_analysis_status", "ai_analysis_error"])

        from .tasks import analyze_repo_with_ai
        analyze_repo_with_ai.delay(repo.id, request.user.id)

        return Response(
            {"detail": "Analysis started.", "status": "pending"},
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, repo_id):
        """GET — Check analysis status / get results."""
        try:
            repo = OrganizationRepo.objects.get(pk=repo_id)
        except OrganizationRepo.DoesNotExist:
            return Response(
                {"detail": "Repository not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(OrganizationRepoSerializer(repo).data)


class ProspectExportView(APIView):
    """GET /api/prospects/export/ — Export saved prospects as CSV."""

    def get(self, request):
        saved = SavedProspect.objects.filter(
            user=request.user
        ).select_related("organization").prefetch_related(
            "organization__repos__stack_detections"
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="prospects.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Organization", "GitHub URL", "Website", "Location",
            "Description", "Status", "Notes", "Tech Stack", "Saved At",
        ])

        for sp in saved:
            org = sp.organization
            # Gather tech stack from all repos
            techs = set()
            for repo in org.repos.prefetch_related("stack_detections").all():
                for det in repo.stack_detections.all():
                    techs.add(det.technology_name)

            writer.writerow([
                org.name or org.github_login,
                org.github_url,
                org.website,
                org.location,
                org.description[:200],
                sp.status,
                sp.notes,
                ", ".join(sorted(techs)),
                sp.created_at.strftime("%Y-%m-%d"),
            ])

        return response
