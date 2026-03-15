import hashlib
import uuid

from django.db import models


class Session(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_hash = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=10)  # desktop, mobile, tablet
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    is_bot = models.BooleanField(default=False)
    country = models.CharField(max_length=2, blank=True, default="")  # ISO 3166-1 alpha-2
    region = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    referrer = models.URLField(blank=True, default="")
    referrer_domain = models.CharField(max_length=253, blank=True, default="")
    screen_width = models.PositiveIntegerField(null=True, blank=True)
    screen_height = models.PositiveIntegerField(null=True, blank=True)
    utm_source = models.CharField(max_length=200, blank=True, default="")
    utm_medium = models.CharField(max_length=200, blank=True, default="")
    utm_campaign = models.CharField(max_length=200, blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(fields=["referrer_domain"]),
            models.Index(fields=["device_type"]),
            models.Index(fields=["is_bot"]),
        ]

    def __str__(self):
        return f"{self.device_type} - {self.browser}/{self.os} - {self.started_at:%Y-%m-%d}"

    @staticmethod
    def make_hash(ip: str, user_agent: str, date_str: str) -> str:
        raw = f"{ip}|{user_agent}|{date_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @property
    def page_view_count(self):
        return self.page_views.count()

    @property
    def duration_seconds(self):
        """Time between first and last page view."""
        views = self.page_views.order_by("viewed_at")
        first = views.first()
        last = views.last()
        if first and last and first != last:
            return (last.viewed_at - first.viewed_at).total_seconds()
        return 0


class PageView(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="page_views")
    path = models.CharField(max_length=500)
    page_title = models.CharField(max_length=300, blank=True, default="")
    time_on_page_seconds = models.FloatField(null=True, blank=True)
    referrer_path = models.CharField(max_length=500, blank=True, default="")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["path", "viewed_at"]),
            models.Index(fields=["viewed_at"]),
        ]

    def __str__(self):
        return f"{self.path} at {self.viewed_at:%Y-%m-%d %H:%M}"
