"""Tests for resume-to-job matching logic."""

import pytest
from django.contrib.auth import get_user_model

from apps.jobs.models import JobListing
from apps.resumes.matching import match_jobs_for_user
from apps.resumes.models import ResumeJobMatch, ResumeProfile

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="matchuser", email="match@example.com", password="test123"
    )


@pytest.fixture
def resume_profile(user):
    return ResumeProfile.objects.create(
        user=user,
        file_type="pdf",
        tech_stack=["Django", "React", "PostgreSQL"],
        summary="Full stack engineer",
    )


@pytest.fixture
def django_job(db):
    return JobListing.objects.create(
        source="remoteok",
        company_name="Django Corp",
        external_id="rok-django-1",
        title="Django Developer",
        apply_url="https://example.com/apply",
        detected_techs=["Django", "Python", "PostgreSQL"],
    )


@pytest.fixture
def react_job(db):
    return JobListing.objects.create(
        source="remotive",
        company_name="React Shop",
        external_id="rem-react-1",
        title="React Engineer",
        apply_url="https://example.com/apply2",
        detected_techs=["React", "TypeScript"],
    )


@pytest.fixture
def rust_job(db):
    return JobListing.objects.create(
        source="wwr",
        company_name="Rust Inc",
        external_id="wwr-rust-1",
        title="Rust Developer",
        apply_url="https://example.com/apply3",
        detected_techs=["Rust", "WebAssembly"],
    )


class TestMatchJobsForUser:
    def test_matches_by_tech_overlap(self, user, resume_profile, django_job, react_job, rust_job):
        count = match_jobs_for_user(user.id)
        assert count == 2  # Django job (2 overlap) + React job (1 overlap), not Rust

        matches = list(ResumeJobMatch.objects.filter(user=user).order_by("-match_score"))
        assert len(matches) == 2

        # Django job has 2 overlapping techs (Django + PostgreSQL)
        assert matches[0].job_id == django_job.id
        assert matches[0].match_score == 2
        assert "django" in matches[0].matched_techs
        assert "postgresql" in matches[0].matched_techs

        # React job has 1 overlapping tech
        assert matches[1].job_id == react_job.id
        assert matches[1].match_score == 1

    def test_no_resume_returns_zero(self, user):
        assert match_jobs_for_user(user.id) == 0

    def test_empty_tech_stack_returns_zero(self, user):
        ResumeProfile.objects.create(
            user=user, file_type="pdf", tech_stack=[]
        )
        assert match_jobs_for_user(user.id) == 0

    def test_rematching_replaces_old_matches(self, user, resume_profile, django_job):
        match_jobs_for_user(user.id)
        assert ResumeJobMatch.objects.filter(user=user).count() == 1

        # Run again — should replace, not duplicate
        match_jobs_for_user(user.id)
        assert ResumeJobMatch.objects.filter(user=user).count() == 1

    def test_inactive_jobs_excluded(self, user, resume_profile, django_job):
        django_job.is_active = False
        django_job.save()

        assert match_jobs_for_user(user.id) == 0


class TestMatchedJobsEndpoint:
    @pytest.fixture
    def api_client(self, user):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_get_matched_jobs(self, api_client, user, resume_profile, django_job, react_job):
        match_jobs_for_user(user.id)

        response = api_client.get("/api/resumes/matched-jobs/")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        # Should include match_score and matched_techs
        assert "match_score" in results[0]
        assert "matched_techs" in results[0]
        # Should include normal job fields
        assert "title" in results[0]
        assert "company_name" in results[0]

    def test_post_triggers_rematching(self, api_client, user, resume_profile, django_job):
        response = api_client.post("/api/resumes/matched-jobs/")
        assert response.status_code == 200
        assert response.json()["matched"] == 1
