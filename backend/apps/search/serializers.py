from rest_framework import serializers

from .models import SearchQuery, SearchPreset, SearchResult


class SearchConfigSerializer(serializers.Serializer):
    """Validates the search configuration JSON."""

    name = serializers.CharField(max_length=200, required=False, default="")
    stack_requirements = serializers.DictField(required=True)
    filters = serializers.DictField(required=False, default=dict)
    max_results = serializers.IntegerField(required=False, default=50, min_value=1, max_value=100)

    def validate_stack_requirements(self, value):
        if "must_have" not in value and "ai_tool_signals" not in value:
            raise serializers.ValidationError(
                "stack_requirements must include 'must_have' or 'ai_tool_signals'"
            )
        return value


class SearchQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = [
            "id", "name", "config", "status", "total_repos_found",
            "total_orgs_found", "error_message", "started_at",
            "completed_at", "created_at",
        ]
        read_only_fields = [
            "id", "status", "total_repos_found", "total_orgs_found",
            "error_message", "started_at", "completed_at", "created_at",
        ]


class SearchPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchPreset
        fields = ["id", "name", "config", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SearchResultSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_login = serializers.CharField(source="organization.github_login", read_only=True)
    organization_avatar = serializers.URLField(source="organization.avatar_url", read_only=True)
    repo_name = serializers.CharField(source="repo.full_name", read_only=True)

    class Meta:
        model = SearchResult
        fields = [
            "id", "match_score", "matched_stack",
            "organization_name", "organization_login", "organization_avatar",
            "repo_name", "created_at",
        ]
