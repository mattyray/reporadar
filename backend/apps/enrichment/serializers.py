from rest_framework import serializers

from .models import OrganizationContact


class OrganizationContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationContact
        fields = [
            "id", "provider", "first_name", "last_name", "email",
            "email_confidence", "email_verified", "position", "department",
            "seniority", "linkedin_url", "is_engineering_lead",
            "last_enriched_at", "created_at",
        ]
