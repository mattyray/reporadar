import uuid

from django.conf import settings
from django.db import models


class SearchQuery(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="searches"
    )
    name = models.CharField(max_length=200, blank=True)
    config = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_repos_found = models.IntegerField(default=0)
    total_orgs_found = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or 'Unnamed'} ({self.status})"


class SearchPreset(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_presets"
    )
    name = models.CharField(max_length=200)
    config = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SearchResult(models.Model):
    search = models.ForeignKey(
        SearchQuery, on_delete=models.CASCADE, related_name="results"
    )
    organization = models.ForeignKey(
        "prospects.Organization", on_delete=models.CASCADE, related_name="search_results"
    )
    repo = models.ForeignKey(
        "prospects.OrganizationRepo", on_delete=models.CASCADE, related_name="search_results"
    )
    match_score = models.IntegerField(default=0)
    matched_stack = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("search", "repo")
        ordering = ["-match_score"]

    def __str__(self):
        return f"{self.organization} — score {self.match_score}"
