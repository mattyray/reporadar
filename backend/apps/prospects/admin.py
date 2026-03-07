from django.contrib import admin

from .models import Organization, OrganizationRepo, RepoContributor, RepoStackDetection, SavedProspect


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("github_login", "name", "location", "public_repos_count", "last_scanned_at")
    search_fields = ("github_login", "name")
    list_filter = ("location",)


@admin.register(OrganizationRepo)
class OrganizationRepoAdmin(admin.ModelAdmin):
    list_display = ("full_name", "stars", "has_claude_md", "has_docker", "has_tests", "last_pushed_at")
    search_fields = ("full_name",)
    list_filter = ("has_claude_md", "has_docker", "has_ci_cd", "has_tests")


@admin.register(RepoStackDetection)
class RepoStackDetectionAdmin(admin.ModelAdmin):
    list_display = ("repo", "technology_name", "category")
    list_filter = ("category",)


@admin.register(RepoContributor)
class RepoContributorAdmin(admin.ModelAdmin):
    list_display = ("github_username", "name", "company", "contributions")
    search_fields = ("github_username", "name", "company")


@admin.register(SavedProspect)
class SavedProspectAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "status", "created_at")
    list_filter = ("status",)
