import uuid

from django.conf import settings
from django.db import models


class OutreachMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ("linkedin_dm", "LinkedIn DM"),
        ("email", "Email"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="outreach_messages"
    )
    organization = models.ForeignKey(
        "prospects.Organization", on_delete=models.CASCADE, related_name="outreach_messages"
    )
    contact = models.ForeignKey(
        "enrichment.OrganizationContact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outreach_messages",
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    context_used = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Outreach to {self.organization} ({self.message_type})"
