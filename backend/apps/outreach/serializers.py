from rest_framework import serializers

from .models import OutreachMessage


class OutreachMessageSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = OutreachMessage
        fields = [
            "id", "organization_name", "message_type", "subject",
            "body", "context_used", "created_at",
        ]


class OutreachGenerateSerializer(serializers.Serializer):
    organization_id = serializers.IntegerField()
    contact_id = serializers.IntegerField(required=False)
    message_type = serializers.ChoiceField(choices=["linkedin_dm", "email", "other"])
