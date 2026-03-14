from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ResumeJobMatch, ResumeProfile
from .serializers import ResumeProfileSerializer, ResumeUploadSerializer


class ResumeUploadView(APIView):
    """POST /api/resumes/upload/ — Upload a resume (PDF/DOCX)."""

    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        file_type = uploaded_file.name.rsplit(".", 1)[-1].lower()

        profile, _ = ResumeProfile.objects.update_or_create(
            user=request.user,
            defaults={
                "original_file": uploaded_file,
                "file_type": file_type,
            },
        )

        # Trigger async parsing with Claude API
        from .tasks import parse_resume
        parse_resume.delay(profile.id)

        return Response(
            ResumeProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )


class ResumeProfileView(APIView):
    """GET/PUT/DELETE /api/resumes/profile/ — Manage parsed resume profile."""

    def get(self, request):
        try:
            profile = ResumeProfile.objects.get(user=request.user)
        except ResumeProfile.DoesNotExist:
            return Response(
                {"detail": "No resume uploaded."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ResumeProfileSerializer(profile).data)

    def put(self, request):
        try:
            profile = ResumeProfile.objects.get(user=request.user)
        except ResumeProfile.DoesNotExist:
            return Response(
                {"detail": "No resume uploaded."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResumeProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        deleted, _ = ResumeProfile.objects.filter(user=request.user).delete()
        if not deleted:
            return Response(
                {"detail": "No resume to delete."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MatchedJobsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MatchedJobsView(APIView):
    """GET /api/resumes/matched-jobs/ — Jobs matching the user's resume."""

    def get(self, request):
        from apps.jobs.serializers import JobListingSerializer

        matches = (
            ResumeJobMatch.objects.filter(user=request.user)
            .select_related("job", "job__ats_mapping", "job__ats_mapping__organization")
            .order_by("-match_score", "-created_at")
        )

        # Manual pagination
        paginator = MatchedJobsPagination()
        page = paginator.paginate_queryset(matches, request)

        results = []
        for match in page:
            job_data = JobListingSerializer(match.job).data
            job_data["match_score"] = match.match_score
            job_data["matched_techs"] = match.matched_techs
            results.append(job_data)

        return paginator.get_paginated_response(results)

    def post(self, request):
        """POST /api/resumes/matched-jobs/ — Trigger re-matching."""
        from .matching import match_jobs_for_user

        count = match_jobs_for_user(request.user.id)
        return Response({"matched": count})
