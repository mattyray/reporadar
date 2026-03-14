from rest_framework import serializers

from .models import ATSMapping, JobListing


class JobListingSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    ats_platform = serializers.SerializerMethodField()
    organization_id = serializers.SerializerMethodField()
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
            "salary",
            "detected_techs",
            "apply_url",
            "is_active",
            "posted_at",
            "last_seen_at",
            "source",
            "source_url",
            "company_name",
            "ats_platform",
            "organization_id",
            "avatar_url",
        ]

    def get_company_name(self, obj):
        return obj.get_company_name()

    def get_ats_platform(self, obj):
        return obj.ats_mapping.ats_platform if obj.ats_mapping else ""

    def get_organization_id(self, obj):
        if obj.ats_mapping and obj.ats_mapping.organization_id:
            return obj.ats_mapping.organization_id
        return None

    def get_avatar_url(self, obj):
        if obj.ats_mapping and obj.ats_mapping.organization:
            return obj.ats_mapping.organization.avatar_url
        return ""


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
