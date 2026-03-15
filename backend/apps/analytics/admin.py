from django.contrib import admin

from .models import PageView, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "device_type", "browser", "os", "is_bot",
        "country", "city", "referrer_domain", "started_at", "last_seen_at",
    ]
    list_filter = ["device_type", "browser", "is_bot", "country"]
    search_fields = ["city", "referrer_domain", "utm_source"]
    readonly_fields = [
        "visitor_hash", "ip_address", "user_agent",
        "screen_width", "screen_height",
        "utm_source", "utm_medium", "utm_campaign",
    ]


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ["id", "path", "page_title", "time_on_page_seconds", "viewed_at"]
    list_filter = ["path"]
    raw_id_fields = ["session"]
