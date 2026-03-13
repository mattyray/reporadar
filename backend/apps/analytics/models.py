import hashlib

from django.db import models


class Session(models.Model):
    session_hash = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=10)  # desktop, mobile, tablet
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    is_bot = models.BooleanField(default=False)
    country = models.CharField(max_length=100, blank=True, default="")
    region = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    referrer = models.URLField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session_hash"],
                name="unique_session_hash",
            )
        ]

    def __str__(self):
        return f"{self.device_type} - {self.browser}/{self.os} - {self.started_at:%Y-%m-%d}"

    @staticmethod
    def make_hash(ip: str, user_agent: str, date_str: str) -> str:
        raw = f"{ip}|{user_agent}|{date_str}"
        return hashlib.sha256(raw.encode()).hexdigest()


class PageView(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="page_views")
    path = models.CharField(max_length=500)
    page_title = models.CharField(max_length=300, blank=True, default="")
    time_on_page_seconds = models.FloatField(null=True, blank=True)
    referrer_path = models.CharField(max_length=500, blank=True, default="")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["viewed_at"]),
            models.Index(fields=["path"]),
        ]

    def __str__(self):
        return f"{self.path} at {self.viewed_at:%Y-%m-%d %H:%M}"
