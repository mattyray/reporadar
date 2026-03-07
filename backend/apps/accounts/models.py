from django.conf import settings
from django.db import models
from encrypted_fields import EncryptedCharField


class APICredential(models.Model):
    PROVIDER_CHOICES = [
        ("hunter", "Hunter.io"),
        ("apollo", "Apollo.io"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_credentials"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    encrypted_key = EncryptedCharField(max_length=500)
    is_valid = models.BooleanField(default=True)
    credits_remaining = models.IntegerField(null=True, blank=True)
    credits_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "provider")

    def __str__(self):
        return f"{self.user.email} — {self.get_provider_display()}"


def get_github_token(user):
    """Get GitHub OAuth token from allauth's SocialToken."""
    from allauth.socialaccount.models import SocialToken

    token = SocialToken.objects.filter(
        account__user=user, account__provider="github"
    ).first()
    return token.token if token else None


def has_github_connected(user):
    """Check if user has connected their GitHub account."""
    from allauth.socialaccount.models import SocialAccount

    return SocialAccount.objects.filter(user=user, provider="github").exists()
