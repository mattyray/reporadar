from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import get_github_token
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


class CompanyLookupView(APIView):
    """GET /api/search/company/?q=ycharts — Search GitHub for orgs/users by name."""

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"detail": "Query must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = get_github_token(request.user)
        if not token:
            return Response(
                {"detail": "GitHub not connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from providers.github_client import GitHubClient
        client = GitHubClient(token=token)
        results = client.search_users(query, per_page=10)

        # Return a clean list
        return Response({
            "results": [
                {
                    "login": r.get("login", ""),
                    "github_id": r.get("id"),
                    "avatar_url": r.get("avatar_url", ""),
                    "type": r.get("type", ""),  # "Organization" or "User"
                    "url": r.get("html_url", ""),
                }
                for r in results
            ]
        })


class CompanyScanView(APIView):
    """POST /api/search/company/scan/ — Scan an org's repos and save to DB."""

    def post(self, request):
        login = request.data.get("login", "").strip()
        if not login:
            return Response(
                {"detail": "login is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = get_github_token(request.user)
        if not token:
            return Response(
                {"detail": "GitHub not connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .tasks import scan_company
        task = scan_company.delay(login, request.user.id)

        return Response(
            {"detail": "Scan started.", "task_id": task.id, "login": login},
            status=status.HTTP_202_ACCEPTED,
        )


class CompanyScanStatusView(APIView):
    """GET /api/search/company/scan/status/?login=ycharts — Check if scan is done."""

    def get(self, request):
        login = request.query_params.get("login", "").strip()
        if not login:
            return Response(
                {"detail": "login param required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.prospects.models import Organization
        try:
            org = Organization.objects.get(github_login__iexact=login)
            from apps.prospects.serializers import OrganizationDetailSerializer
            return Response({
                "status": "completed",
                "organization": OrganizationDetailSerializer(org).data,
            })
        except Organization.DoesNotExist:
            return Response({"status": "scanning"})


class SearchPresetListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/search/presets/ — List or create search presets."""

    serializer_class = SearchPresetSerializer

    def get_queryset(self):
        return SearchPreset.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
