from django.contrib import admin

from .models import APICredential


@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "is_valid", "credits_remaining", "updated_at")
    list_filter = ("provider", "is_valid")
    readonly_fields = ("encrypted_key",)
