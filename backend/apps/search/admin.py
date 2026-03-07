from django.contrib import admin

from .models import SearchQuery, SearchPreset, SearchResult


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "status", "total_repos_found", "total_orgs_found", "created_at")
    list_filter = ("status",)


@admin.register(SearchPreset)
class SearchPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ("search", "organization", "match_score")
    list_filter = ("match_score",)
