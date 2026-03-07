from rest_framework import serializers

from .models import ATSMapping, JobListing


class JobListingSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="ats_mapping.company_name", read_only=True)
    ats_platform = serializers.CharField(source="ats_mapping.ats_platform", read_only=True)
    organization_id = serializers.IntegerField(
        source="ats_mapping.organization_id", read_only=True
    )
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            "id",
            "external_id",
            "title",
            "department",
            "location",
            "employment_type",
            "detected_techs",
            "apply_url",
            "is_active",
            "posted_at",
            "last_seen_at",
            "company_name",
            "ats_platform",
            "organization_id",
            "avatar_url",
        ]

    def get_avatar_url(self, obj):
        org = obj.ats_mapping.organization
        return org.avatar_url if org else ""


class ATSMappingSerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = ATSMapping
        fields = [
            "id",
            "company_name",
            "ats_platform",
            "ats_slug",
            "is_verified",
            "last_checked_at",
            "organization",
            "job_count",
        ]

    def get_job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()
