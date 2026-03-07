from django.contrib import admin

from .models import OutreachMessage


@admin.register(OutreachMessage)
class OutreachMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "message_type", "created_at")
    list_filter = ("message_type",)
