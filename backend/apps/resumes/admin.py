from django.contrib import admin

from .models import ResumeProfile


@admin.register(ResumeProfile)
class ResumeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "file_type", "years_experience", "parsed_at", "created_at")
