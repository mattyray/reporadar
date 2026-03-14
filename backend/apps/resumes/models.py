from django.conf import settings
from django.db import models


class ResumeProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_profile"
    )
    original_file = models.FileField(upload_to="resumes/")
    file_type = models.CharField(max_length=10)
    parsed_data = models.JSONField(default=dict)
    summary = models.TextField(blank=True)
    key_projects = models.JSONField(default=list)
    tech_stack = models.JSONField(default=list)
    years_experience = models.IntegerField(null=True, blank=True)
    story_hook = models.TextField(blank=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume: {self.user.email}"


class ResumeJobMatch(models.Model):
    """A job that matches a user's resume tech stack."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_matches"
    )
    job = models.ForeignKey(
        "jobs.JobListing", on_delete=models.CASCADE, related_name="resume_matches"
    )
    match_score = models.IntegerField(default=0)
    matched_techs = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-match_score"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.job.title} ({self.match_score})"
