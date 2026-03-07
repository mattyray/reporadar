from django.db import models


class ATSMapping(models.Model):
    """Maps a company (optionally linked to a GitHub Organization) to its ATS job board."""

    ATS_CHOICES = [
        ("greenhouse", "Greenhouse"),
        ("lever", "Lever"),
        ("ashby", "Ashby"),
        ("workable", "Workable"),
    ]

    organization = models.ForeignKey(
        "prospects.Organization",
        on_delete=models.CASCADE,
        related_name="ats_mappings",
        null=True,
        blank=True,
    )
    company_name = models.CharField(max_length=200)
    ats_platform = models.CharField(max_length=20, choices=ATS_CHOICES)
    ats_slug = models.CharField(max_length=200)
    is_verified = models.BooleanField(default=False)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ats_platform", "ats_slug")
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return f"{self.company_name} ({self.ats_platform}: {self.ats_slug})"


class JobListing(models.Model):
    """A cached job posting from an ATS platform."""

    ats_mapping = models.ForeignKey(
        ATSMapping, on_delete=models.CASCADE, related_name="jobs"
    )
    external_id = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    department = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=300, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    description_text = models.TextField(blank=True)
    apply_url = models.URLField(max_length=500)
    detected_techs = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ats_mapping", "external_id")
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.ats_mapping.company_name}"
