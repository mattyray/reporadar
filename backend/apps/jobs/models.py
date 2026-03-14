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
    """A cached job posting from an ATS platform or external job board."""

    SOURCE_CHOICES = [
        ("ats", "ATS Board"),
        ("remoteok", "RemoteOK"),
        ("remotive", "Remotive"),
        ("wwr", "We Work Remotely"),
        ("hn", "HackerNews Who's Hiring"),
    ]

    ats_mapping = models.ForeignKey(
        ATSMapping,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="ats")
    source_url = models.URLField(max_length=500, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    external_id = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    department = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=300, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    salary = models.CharField(max_length=200, blank=True)
    description_text = models.TextField(blank=True)
    apply_url = models.URLField(max_length=500)
    detected_techs = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["source"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["ats_mapping", "external_id"],
                condition=models.Q(ats_mapping__isnull=False),
                name="unique_ats_job",
            ),
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=models.Q(ats_mapping__isnull=True),
                name="unique_external_job",
            ),
        ]

    def __str__(self):
        name = self.company_name or (
            self.ats_mapping.company_name if self.ats_mapping else "Unknown"
        )
        return f"{self.title} at {name}"

    def get_company_name(self):
        """Return company name from direct field or ATS mapping."""
        return self.company_name or (
            self.ats_mapping.company_name if self.ats_mapping else ""
        )
