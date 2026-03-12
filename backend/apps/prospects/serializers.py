from rest_framework import serializers

from .models import Organization, OrganizationRepo, RepoContributor, RepoStackDetection, SavedProspect


class RepoStackDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepoStackDetection
        fields = ["technology_name", "category", "source_file"]


class RepoContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepoContributor
        fields = [
            "github_username", "name", "email", "company", "bio",
            "location", "avatar_url", "contributions", "profile_url",
        ]


class OrganizationRepoSerializer(serializers.ModelSerializer):
    stack_detections = RepoStackDetectionSerializer(many=True, read_only=True)

    class Meta:
        model = OrganizationRepo
        fields = [
            "id", "name", "full_name", "description", "url", "stars", "forks",
            "has_claude_md", "has_cursor_config", "has_copilot_config",
            "has_windsurf_config", "has_aider_config", "has_codeium_config",
            "has_continue_config", "has_bolt_config", "has_v0_config",
            "has_lovable_config", "has_idx_config", "has_amazonq_config",
            "has_cline_config", "has_roo_config", "has_codex_config",
            "has_docker", "has_ci_cd", "has_tests", "has_deployment_config",
            "last_pushed_at", "stack_detections",
        ]


class OrganizationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id", "github_login", "name", "description", "website",
            "location", "avatar_url", "public_repos_count", "github_url",
        ]


class OrganizationDetailSerializer(serializers.ModelSerializer):
    repos = OrganizationRepoSerializer(many=True, read_only=True)
    top_contributors = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id", "github_login", "name", "description", "website", "email",
            "location", "blog", "avatar_url", "public_repos_count", "github_url",
            "careers_url", "linkedin_search_url", "last_scanned_at",
            "repos", "top_contributors",
        ]

    def get_top_contributors(self, obj):
        # Use prefetched data instead of a separate query
        all_contributors = []
        for repo in obj.repos.all():
            all_contributors.extend(repo.contributors.all())
        # Deduplicate by github_username, keep highest contribution count
        seen = {}
        for c in all_contributors:
            if c.github_username not in seen or c.contributions > seen[c.github_username].contributions:
                seen[c.github_username] = c
        top = sorted(seen.values(), key=lambda c: c.contributions, reverse=True)[:10]
        return RepoContributorSerializer(top, many=True).data


class SavedProspectSerializer(serializers.ModelSerializer):
    organization = OrganizationListSerializer(read_only=True)

    class Meta:
        model = SavedProspect
        fields = ["id", "organization", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
