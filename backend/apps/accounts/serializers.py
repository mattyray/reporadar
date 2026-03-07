from rest_framework import serializers

from .models import APICredential


class UserProfileSerializer(serializers.Serializer):
    """Current user profile + connected services status."""

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    github_connected = serializers.BooleanField(read_only=True)
    has_hunter_key = serializers.BooleanField(read_only=True)
    has_apollo_key = serializers.BooleanField(read_only=True)


class APICredentialSerializer(serializers.ModelSerializer):
    """For listing/viewing API credentials (never exposes the actual key)."""

    class Meta:
        model = APICredential
        fields = [
            "id", "provider", "is_valid", "credits_remaining",
            "credits_checked_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class APICredentialCreateSerializer(serializers.Serializer):
    """For creating/updating API credentials."""

    provider = serializers.ChoiceField(choices=["hunter", "apollo"])
    api_key = serializers.CharField(max_length=500)
