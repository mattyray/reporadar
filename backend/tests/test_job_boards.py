"""Tests for external job board providers and tasks."""

import pytest
import responses

from providers.job_boards import (
    ExternalJobPost,
    _parse_hn_comment,
    _strip_html,
    fetch_remoteok_jobs,
    fetch_remotive_jobs,
)


class TestHNCommentParsing:
    def test_standard_format(self):
        text = "Acme Corp | Senior Engineer | San Francisco, CA | REMOTE | Full Time\n\nWe're building..."
        result = _parse_hn_comment(text)
        assert result["company"] == "Acme Corp"
        assert result["role"] == "Senior Engineer"
        assert "location" in result

    def test_company_and_role_only(self):
        text = "StartupXYZ | Backend Developer\n\nApply at https://example.com/jobs"
        result = _parse_hn_comment(text)
        assert result["company"] == "StartupXYZ"
        assert result["role"] == "Backend Developer"
        assert result["apply_url"] == "https://example.com/jobs"

    def test_remote_detection(self):
        text = "CoolCo | Engineer | Remote\n\nDescription here"
        result = _parse_hn_comment(text)
        assert result["company"] == "CoolCo"
        assert result["location"] == "Remote"

    def test_no_pipe_returns_none(self):
        text = "This is just a regular comment without pipes"
        assert _parse_hn_comment(text) is None

    def test_empty_returns_none(self):
        assert _parse_hn_comment("") is None

    def test_url_extraction(self):
        text = "Company | Role\n\nApply here: https://jobs.company.com/apply?id=123"
        result = _parse_hn_comment(text)
        assert result["apply_url"] == "https://jobs.company.com/apply?id=123"


class TestStripHtml:
    def test_strips_tags(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_empty(self):
        assert _strip_html("") == ""

    def test_plain_text(self):
        assert _strip_html("no tags here") == "no tags here"


class TestRemoteOKFetch:
    @responses.activate
    def test_fetch_success(self):
        responses.add(
            responses.GET,
            "https://remoteok.com/api",
            json=[
                {"legal": "notice"},  # First item is metadata
                {
                    "id": 12345,
                    "company": "TestCorp",
                    "position": "Django Developer",
                    "location": "Worldwide",
                    "description": "<p>Build stuff with Django</p>",
                    "url": "https://remoteok.com/jobs/12345",
                    "apply_url": "https://testcorp.com/apply",
                    "date": "2026-03-10T00:00:00",
                    "salary_min": 120000,
                    "salary_max": 180000,
                    "tags": ["python", "django", "react"],
                },
            ],
            status=200,
        )

        jobs = fetch_remoteok_jobs()
        assert len(jobs) == 1
        assert jobs[0].company_name == "TestCorp"
        assert jobs[0].title == "Django Developer"
        assert jobs[0].external_id == "rok-12345"
        assert jobs[0].source == "remoteok"
        assert jobs[0].salary == "$120,000 - $180,000"
        assert "python" in jobs[0].tags

    @responses.activate
    def test_fetch_failure(self):
        responses.add(responses.GET, "https://remoteok.com/api", status=500)
        jobs = fetch_remoteok_jobs()
        assert jobs == []


class TestRemotiveFetch:
    @responses.activate
    def test_fetch_success(self):
        responses.add(
            responses.GET,
            "https://remotive.com/api/remote-jobs",
            json={
                "job-count": 1,
                "jobs": [
                    {
                        "id": 67890,
                        "title": "React Engineer",
                        "company_name": "RemotiveInc",
                        "candidate_required_location": "USA",
                        "job_type": "full_time",
                        "salary": "$100k - $140k",
                        "description": "<div>React and TypeScript</div>",
                        "url": "https://remotive.com/jobs/67890",
                        "publication_date": "2026-03-12T00:00:00",
                    }
                ],
            },
            status=200,
        )

        jobs = fetch_remotive_jobs()
        assert len(jobs) == 1
        assert jobs[0].company_name == "RemotiveInc"
        assert jobs[0].external_id == "rem-67890"
        assert jobs[0].employment_type == "Full-time"
        assert jobs[0].source == "remotive"


class TestStoreExternalJobs:
    @pytest.mark.django_db
    def test_store_and_dedup(self):
        """External jobs are stored and deduplicated by source+external_id."""
        from apps.jobs.models import JobListing
        from apps.jobs.tasks import _store_external_jobs

        jobs = [
            ExternalJobPost(
                external_id="rok-1",
                source="remoteok",
                company_name="TestCo",
                title="Engineer",
                description_text="Python and Django developer needed",
                apply_url="https://example.com/apply",
            ),
        ]

        _store_external_jobs(jobs)
        assert JobListing.objects.filter(source="remoteok").count() == 1

        # Store again — should update, not duplicate
        _store_external_jobs(jobs)
        assert JobListing.objects.filter(source="remoteok").count() == 1

        # Verify fields
        listing = JobListing.objects.get(source="remoteok", external_id="rok-1")
        assert listing.company_name == "TestCo"
        assert listing.ats_mapping is None
        assert "Python" in listing.detected_techs
        assert "Django" in listing.detected_techs

    @pytest.mark.django_db
    def test_stale_jobs_marked_inactive(self):
        """Jobs not seen in latest fetch are marked inactive."""
        from apps.jobs.models import JobListing
        from apps.jobs.tasks import _store_external_jobs

        # First fetch: 2 jobs
        jobs = [
            ExternalJobPost(
                external_id="rok-1", source="remoteok",
                company_name="A", title="Job A", apply_url="https://a.com",
            ),
            ExternalJobPost(
                external_id="rok-2", source="remoteok",
                company_name="B", title="Job B", apply_url="https://b.com",
            ),
        ]
        _store_external_jobs(jobs)
        assert JobListing.objects.filter(source="remoteok", is_active=True).count() == 2

        # Second fetch: only 1 job
        _store_external_jobs(jobs[:1])
        assert JobListing.objects.filter(source="remoteok", is_active=True).count() == 1
        assert JobListing.objects.filter(source="remoteok", is_active=False).count() == 1
