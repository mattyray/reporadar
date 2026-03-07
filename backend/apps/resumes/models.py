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
