from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ResumeProfile
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

        # TODO: trigger Celery task to parse with Claude API
        # from .tasks import parse_resume
        # parse_resume.delay(profile.id)

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
