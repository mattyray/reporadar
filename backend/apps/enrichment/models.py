from django.conf import settings
from django.db import models


class OrganizationContact(models.Model):
    PROVIDER_CHOICES = [
        ("hunter", "Hunter.io"),
        ("apollo", "Apollo.io"),
        ("github", "GitHub"),
    ]

    organization = models.ForeignKey(
        "prospects.Organization", on_delete=models.CASCADE, related_name="contacts"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    email_confidence = models.IntegerField(default=0)
    email_verified = models.BooleanField(default=False)
    position = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=100, blank=True)
    seniority = models.CharField(max_length=50, blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_engineering_lead = models.BooleanField(default=False)
    source_domain = models.CharField(max_length=200)
    last_enriched_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_engineering_lead"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class EnrichmentLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrichment_logs"
    )
    provider = models.CharField(max_length=20)
    endpoint = models.CharField(max_length=100)
    domain_searched = models.CharField(max_length=200)
    credits_used = models.DecimalField(max_digits=5, decimal_places=1)
    results_returned = models.IntegerField(default=0)
    cached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider}:{self.endpoint} — {self.domain_searched}"
