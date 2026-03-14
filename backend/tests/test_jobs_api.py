"""Tests for jobs API endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.jobs.models import ATSMapping, JobListing
from apps.prospects.models import Organization

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org(db):
    return Organization.objects.create(
        github_login="acme-corp",
        github_id=12345,
        name="Acme Corporation",
        description="Building cool stuff",
        website="https://acme.com",
        github_url="https://github.com/acme-corp",
    )


@pytest.fixture
def ats_mapping(org):
    return ATSMapping.objects.create(
        organization=org,
        company_name="Acme Corporation",
        ats_platform="greenhouse",
        ats_slug="acme-corp",
        is_verified=True,
    )


@pytest.fixture
def job_listing(ats_mapping):
    return JobListing.objects.create(
        ats_mapping=ats_mapping,
        external_id="job-123",
        title="Senior Django Engineer",
        department="Engineering",
        location="Remote",
        employment_type="Full-time",
        description_text="We use Django, React, and PostgreSQL",
        apply_url="https://boards.greenhouse.io/acme/jobs/123",
        detected_techs=["Django", "React", "PostgreSQL"],
        is_active=True,
    )


class TestOrgJobsView:
    def test_list_org_jobs(self, api_client, org, job_listing):
        response = api_client.get(f"/api/jobs/org/{org.id}/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Senior Django Engineer"
        assert data["results"][0]["company_name"] == "Acme Corporation"
        assert "Django" in data["results"][0]["detected_techs"]

    def test_list_org_jobs_empty(self, api_client, org):
        response = api_client.get(f"/api/jobs/org/{org.id}/")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0

    def test_inactive_jobs_excluded(self, api_client, org, ats_mapping):
        JobListing.objects.create(
            ats_mapping=ats_mapping,
            external_id="old-job",
            title="Old Position",
            apply_url="https://example.com",
            is_active=False,
        )
        response = api_client.get(f"/api/jobs/org/{org.id}/")
        assert len(response.json()["results"]) == 0


class TestJobSearchView:
    def test_search_all_jobs(self, api_client, job_listing):
        response = api_client.get("/api/jobs/")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_by_tech(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?techs=Django")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_by_tech_no_match(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?techs=Rust")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0

    def test_search_by_location(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?location=Remote")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_by_location_no_match(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?location=Mars")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 0

    def test_search_by_title(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?title=Django")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_combined_filters(self, api_client, job_listing):
        response = api_client.get("/api/jobs/?techs=Django&location=Remote")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1


class TestOrgJobsCheckView:
    def test_check_nonexistent_org(self, api_client):
        response = api_client.post("/api/jobs/org/99999/check/")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_check_triggers_probe(self, api_client, org, settings):
        settings.CELERY_TASK_ALWAYS_EAGER = True
        # Without mocking the ATS APIs, the probe will fail silently
        # but should still return a probing status
        response = api_client.post(f"/api/jobs/org/{org.id}/check/")
        assert response.status_code == 200
        assert response.json()["status"] in ("probing", "cached")


class TestATSMappingModel:
    def test_str(self, ats_mapping):
        assert "Acme Corporation" in str(ats_mapping)
        assert "greenhouse" in str(ats_mapping)

    def test_unique_together(self, ats_mapping, org):
        with pytest.raises(Exception):
            ATSMapping.objects.create(
                organization=org,
                company_name="Dupe",
                ats_platform="greenhouse",
                ats_slug="acme-corp",
            )


class TestJobListingModel:
    def test_str(self, job_listing):
        assert "Senior Django Engineer" in str(job_listing)
        assert "Acme" in str(job_listing)

    def test_unique_together(self, ats_mapping, job_listing):
        with pytest.raises(Exception):
            JobListing.objects.create(
                ats_mapping=ats_mapping,
                external_id="job-123",
                title="Duplicate",
                apply_url="https://example.com",
            )

    def test_external_job_no_ats_mapping(self, db):
        """External job boards don't need an ATS mapping."""
        job = JobListing.objects.create(
            ats_mapping=None,
            source="remoteok",
            source_url="https://remoteok.com/jobs/123",
            company_name="Cool Startup",
            external_id="remoteok-123",
            title="Backend Engineer",
            location="Remote",
            apply_url="https://remoteok.com/apply/123",
            detected_techs=["Python", "Django"],
        )
        assert job.get_company_name() == "Cool Startup"
        assert str(job) == "Backend Engineer at Cool Startup"

    def test_external_job_unique_constraint(self, db):
        """External jobs are unique by (source, external_id)."""
        JobListing.objects.create(
            source="remoteok",
            company_name="Startup A",
            external_id="rok-456",
            title="Engineer",
            apply_url="https://example.com",
        )
        with pytest.raises(Exception):
            JobListing.objects.create(
                source="remoteok",
                company_name="Startup B",
                external_id="rok-456",
                title="Duplicate",
                apply_url="https://example.com",
            )


class TestJobSearchSourceFilter:
    def test_filter_by_source(self, api_client, job_listing, db):
        """Filter jobs by source."""
        JobListing.objects.create(
            source="remoteok",
            company_name="Remote Co",
            external_id="rok-1",
            title="React Developer",
            apply_url="https://remoteok.com/apply/1",
            detected_techs=["React"],
        )
        # Filter for remoteok only
        response = api_client.get("/api/jobs/?source=remoteok")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["source"] == "remoteok"

        # Filter for ats only
        response = api_client.get("/api/jobs/?source=ats")
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["source"] == "ats"

        # No filter returns all
        response = api_client.get("/api/jobs/")
        assert len(response.json()["results"]) == 2

    def test_serializer_includes_source_fields(self, api_client, db):
        """Serializer includes source and source_url for external jobs."""
        JobListing.objects.create(
            source="remotive",
            source_url="https://remotive.com/jobs/123",
            company_name="Remotive Co",
            external_id="rem-1",
            title="Django Dev",
            apply_url="https://remotive.com/apply/1",
            salary="$120k - $150k",
            detected_techs=["Django"],
        )
        response = api_client.get("/api/jobs/?source=remotive")
        job = response.json()["results"][0]
        assert job["source"] == "remotive"
        assert job["source_url"] == "https://remotive.com/jobs/123"
        assert job["salary"] == "$120k - $150k"
        assert job["company_name"] == "Remotive Co"


class TestSlugCandidateGeneration:
    """Test ATS slug candidate generation logic."""

    def test_basic_github_login(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("acme", None)
        assert candidates == ["acme"]

    def test_name_variants(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("acme-corp", "Acme Corp")
        assert "acme-corp" in candidates
        assert "acmecorp" in candidates
        assert "acme" in candidates  # first word

    def test_strips_corporate_suffixes(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("stripe", "Stripe Inc")
        assert "stripe" in candidates
        # "stripeinc" should be there as basic variant
        assert "stripeinc" in candidates
        # Should also have suffix-stripped variant (just "stripe")
        assert candidates.count("stripe") == 1  # no duplicates

    def test_strips_llc(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("cool-tech", "Cool Tech LLC")
        assert "cooltech" in candidates
        assert "cool-tech" in candidates
        assert "cool" in candidates  # first word

    def test_multi_word_company(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("palo-alto", "Palo Alto Networks Inc")
        assert "palo-alto" in candidates
        assert "paloaltonetworks" in candidates  # no spaces, no suffix
        assert "paloaltonetworksinc" in candidates  # all words
        assert "palo-alto-networks" in candidates  # stripped suffix hyphenated

    def test_no_duplicates(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("stripe", "Stripe")
        assert len(candidates) == len(set(candidates))

    def test_filters_short_slugs(self):
        from apps.jobs.tasks import _generate_slug_candidates
        candidates = _generate_slug_candidates("ab", "A B Corp")
        # "a" and "b" are too short (< 2 chars), should be filtered
        assert all(len(c) >= 2 for c in candidates)
