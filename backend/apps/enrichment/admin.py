from django.contrib import admin

from .models import EnrichmentLog, OrganizationContact


@admin.register(OrganizationContact)
class OrganizationContactAdmin(admin.ModelAdmin):
    list_display = ("organization", "first_name", "last_name", "email", "position", "is_engineering_lead")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("provider", "is_engineering_lead")


@admin.register(EnrichmentLog)
class EnrichmentLogAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "endpoint", "domain_searched", "credits_used", "created_at")
    list_filter = ("provider",)
