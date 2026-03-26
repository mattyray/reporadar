from django.contrib import admin

from .models import Event, PageView, Session


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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["id", "event_type", "category", "label", "value", "user", "created_at"]
    list_filter = ["category", "event_type"]
    search_fields = ["label", "event_type"]
    raw_id_fields = ["session", "user"]
    readonly_fields = ["metadata"]
