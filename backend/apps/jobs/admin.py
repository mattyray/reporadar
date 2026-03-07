from django.contrib import admin

from .models import ATSMapping, JobListing


@admin.register(ATSMapping)
class ATSMappingAdmin(admin.ModelAdmin):
    list_display = ("company_name", "ats_platform", "ats_slug", "is_verified", "last_checked_at")
    list_filter = ("ats_platform", "is_verified")
    search_fields = ("company_name", "ats_slug")


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "department", "location", "is_active")
    list_filter = ("is_active", "ats_mapping__ats_platform")
    search_fields = ("title", "description_text")

    def company_name(self, obj):
        return obj.ats_mapping.company_name
