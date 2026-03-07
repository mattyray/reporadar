from rest_framework import serializers

from .models import ResumeProfile


class ResumeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeProfile
        fields = [
            "id", "file_type", "parsed_data", "summary", "key_projects",
            "tech_stack", "years_experience", "story_hook",
            "parsed_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "parsed_data", "summary", "key_projects", "tech_stack",
            "years_experience", "story_hook", "parsed_at", "created_at", "updated_at",
        ]


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        ext = value.name.rsplit(".", 1)[-1].lower()
        if ext not in ("pdf", "docx"):
            raise serializers.ValidationError("Only PDF and DOCX files are supported.")
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("File too large. Max 10MB.")
        return value
