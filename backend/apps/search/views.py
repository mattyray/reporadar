from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SearchQuery, SearchPreset, SearchResult
from .serializers import (
    SearchConfigSerializer,
    SearchPresetSerializer,
    SearchQuerySerializer,
    SearchResultSerializer,
)


class SearchCreateView(APIView):
    """POST /api/search/ — Start a new search. Returns job ID for polling."""

    def post(self, request):
        config_serializer = SearchConfigSerializer(data=request.data)
        config_serializer.is_valid(raise_exception=True)

        search = SearchQuery.objects.create(
            user=request.user,
            name=config_serializer.validated_data.get("name", ""),
            config=config_serializer.validated_data,
            status="pending",
        )

        from .tasks import scan_search_results

        task = scan_search_results.delay(str(search.id))
        search.celery_task_id = task.id if task.id else ""
        search.save(update_fields=["celery_task_id"])

        # Refresh from DB in case the task ran synchronously (eager mode)
        search.refresh_from_db()

        return Response(
            SearchQuerySerializer(search).data,
            status=status.HTTP_201_CREATED,
        )


class SearchStatusView(generics.RetrieveAPIView):
    """GET /api/search/{id}/status/ — Poll search job status."""

    serializer_class = SearchQuerySerializer
    lookup_field = "id"

    def get_queryset(self):
        return SearchQuery.objects.filter(user=self.request.user)


class SearchResultsView(generics.ListAPIView):
    """GET /api/search/{id}/results/ — Get search results."""

    serializer_class = SearchResultSerializer

    def get_queryset(self):
        search_id = self.kwargs["id"]
        return SearchResult.objects.filter(
            search_id=search_id, search__user=self.request.user
        ).select_related("organization", "repo")


class SearchHistoryView(generics.ListAPIView):
    """GET /api/search/history/ — Past searches."""

    serializer_class = SearchQuerySerializer

    def get_queryset(self):
        return SearchQuery.objects.filter(user=self.request.user)


class SearchPresetListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/search/presets/ — List or create search presets."""

    serializer_class = SearchPresetSerializer

    def get_queryset(self):
        return SearchPreset.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
