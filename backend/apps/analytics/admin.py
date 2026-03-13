from django.contrib import admin

from .models import PageView, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id", "device_type", "browser", "os", "is_bot", "started_at", "last_seen_at"]
    list_filter = ["device_type", "browser", "is_bot"]
    readonly_fields = ["session_hash", "ip_address", "user_agent"]


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ["id", "path", "page_title", "time_on_page_seconds", "viewed_at"]
    list_filter = ["path"]
    raw_id_fields = ["session"]
