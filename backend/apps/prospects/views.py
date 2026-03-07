from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, SavedProspect
from .serializers import (
    OrganizationDetailSerializer,
    OrganizationListSerializer,
    SavedProspectSerializer,
)


class ProspectListView(generics.ListAPIView):
    """GET /api/prospects/ — List all discovered organizations."""

    serializer_class = OrganizationListSerializer
    queryset = Organization.objects.all().order_by("-updated_at")


class ProspectDetailView(generics.RetrieveAPIView):
    """GET /api/prospects/{id}/ — Organization detail with repos and contributors."""

    serializer_class = OrganizationDetailSerializer
    queryset = Organization.objects.all()


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
    """DELETE /api/prospects/saved/{id}/ — Remove from saved."""

    def get_queryset(self):
        return SavedProspect.objects.filter(user=self.request.user)
