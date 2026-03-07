from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APICredential, has_github_connected
from .serializers import (
    APICredentialCreateSerializer,
    APICredentialSerializer,
    UserProfileSerializer,
)


class UserProfileView(APIView):
    """GET /api/accounts/me/ — Current user profile + connected services."""

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "github_connected": has_github_connected(user),
            "has_hunter_key": APICredential.objects.filter(
                user=user, provider="hunter", is_valid=True
            ).exists(),
            "has_apollo_key": APICredential.objects.filter(
                user=user, provider="apollo", is_valid=True
            ).exists(),
        }
        return Response(UserProfileSerializer(data).data)


class APIKeyListCreateView(APIView):
    """GET/POST /api/accounts/api-keys/ — List or add API keys."""

    def get(self, request):
        credentials = APICredential.objects.filter(user=request.user)
        return Response(APICredentialSerializer(credentials, many=True).data)

    def post(self, request):
        serializer = APICredentialCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        credential, created = APICredential.objects.update_or_create(
            user=request.user,
            provider=serializer.validated_data["provider"],
            defaults={
                "encrypted_key": serializer.validated_data["api_key"],
                "is_valid": True,
                "credits_remaining": None,
                "credits_checked_at": None,
            },
        )

        return Response(
            APICredentialSerializer(credential).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class APIKeyDeleteView(APIView):
    """DELETE /api/accounts/api-keys/{provider}/ — Remove an API key."""

    def delete(self, request, provider):
        deleted, _ = APICredential.objects.filter(
            user=request.user, provider=provider
        ).delete()
        if not deleted:
            return Response(
                {"detail": "No key found for this provider."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIKeyStatusView(APIView):
    """GET /api/accounts/api-keys/status/ — Check credit balances."""

    def get(self, request):
        from providers.hunter import HunterProvider

        results = {}
        credentials = APICredential.objects.filter(user=request.user, is_valid=True)

        for cred in credentials:
            try:
                if cred.provider == "hunter":
                    provider = HunterProvider()
                    credits = provider.check_credits(cred.encrypted_key)
                    results["hunter"] = credits
                    cred.credits_remaining = credits["total"] - credits["used"]
                    cred.credits_checked_at = timezone.now()
                    cred.save(update_fields=["credits_remaining", "credits_checked_at"])
            except Exception as e:
                results[cred.provider] = {"error": str(e)}

        return Response(results)
