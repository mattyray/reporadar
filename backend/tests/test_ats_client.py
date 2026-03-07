"""Tests for ATS client provider with mocked HTTP responses."""

import json

import pytest
import responses

from providers.ats_client import ATSClient, _strip_html


class TestStripHtml:
    def test_basic_tags(self):
        assert _strip_html("<p>Hello</p>") == "Hello"

    def test_nested_tags(self):
        assert _strip_html("<div><p>Hello <strong>World</strong></p></div>") == "Hello World"

    def test_empty_string(self):
        assert _strip_html("") == ""

    def test_no_tags(self):
        assert _strip_html("plain text") == "plain text"


class TestGreenhouseFetch:
    @responses.activate
    def test_fetch_greenhouse_jobs(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/testco/jobs?content=true",
            json={
                "jobs": [
                    {
                        "id": 123,
                        "title": "Senior Django Engineer",
                        "location": {"name": "Remote"},
                        "departments": [{"name": "Engineering"}],
                        "content": "<p>We use Django and React.</p>",
                        "absolute_url": "https://boards.greenhouse.io/testco/jobs/123",
                        "updated_at": "2026-03-01T00:00:00Z",
                    }
                ]
            },
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_greenhouse_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0].title == "Senior Django Engineer"
        assert jobs[0].location == "Remote"
        assert jobs[0].department == "Engineering"
        assert "Django" in jobs[0].description_text
        assert jobs[0].apply_url == "https://boards.greenhouse.io/testco/jobs/123"

    @responses.activate
    def test_fetch_greenhouse_404(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/nonexistent/jobs?content=true",
            status=404,
        )

        client = ATSClient()
        jobs = client.fetch_greenhouse_jobs("nonexistent")
        assert jobs == []


class TestLeverFetch:
    @responses.activate
    def test_fetch_lever_jobs(self):
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/testco?mode=json",
            json=[
                {
                    "id": "abc-123",
                    "text": "Frontend Engineer",
                    "descriptionPlain": "Building with React and TypeScript",
                    "lists": [],
                    "additionalPlain": "",
                    "categories": {
                        "location": "San Francisco",
                        "department": "Engineering",
                        "team": "Frontend",
                        "commitment": "Full-time",
                    },
                    "hostedUrl": "https://jobs.lever.co/testco/abc-123",
                }
            ],
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_lever_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0].title == "Frontend Engineer"
        assert jobs[0].location == "San Francisco"
        assert jobs[0].employment_type == "Full-time"

    @responses.activate
    def test_fetch_lever_empty(self):
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/nonexistent?mode=json",
            json=[],
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_lever_jobs("nonexistent")
        assert jobs == []


class TestAshbyFetch:
    @responses.activate
    def test_fetch_ashby_jobs(self):
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/testco",
            json={
                "jobs": [
                    {
                        "id": "ash-456",
                        "title": "Backend Engineer",
                        "department": "Platform",
                        "location": "Remote, US",
                        "employmentType": "FullTime",
                        "descriptionHtml": "<p>Python and FastAPI</p>",
                        "jobUrl": "https://jobs.ashbyhq.com/testco/ash-456",
                        "publishedAt": "2026-03-01T00:00:00Z",
                    }
                ]
            },
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_ashby_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0].title == "Backend Engineer"
        assert jobs[0].department == "Platform"
        assert "Python" in jobs[0].description_text


class TestWorkableFetch:
    @responses.activate
    def test_fetch_workable_jobs(self):
        responses.add(
            responses.GET,
            "https://apply.workable.com/api/v1/widget/accounts/testco",
            json={
                "jobs": [
                    {
                        "shortcode": "WK789",
                        "title": "DevOps Engineer",
                        "department": "Infrastructure",
                        "location": {
                            "city": "London",
                            "region": "",
                            "country": "UK",
                        },
                        "url": "https://apply.workable.com/testco/j/WK789/",
                    }
                ]
            },
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_workable_jobs("testco")
        assert len(jobs) == 1
        assert jobs[0].title == "DevOps Engineer"
        assert "London" in jobs[0].location
        assert "UK" in jobs[0].location


class TestProbeCompany:
    @responses.activate
    def test_probe_finds_greenhouse(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            json={"jobs": [{"id": 1, "title": "Engineer"}]},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.lever.co/v0/postings/stripe?mode=json",
            json=[],
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.ashbyhq.com/posting-api/job-board/stripe",
            status=404,
        )
        responses.add(
            responses.GET,
            "https://apply.workable.com/api/v1/widget/accounts/stripe",
            status=404,
        )

        client = ATSClient()
        results = client.probe_company("stripe")
        assert results["greenhouse"] is True
        assert results["lever"] is False  # Empty list = not found
        assert results["ashby"] is False
        assert results["workable"] is False


class TestFetchJobs:
    @responses.activate
    def test_fetch_jobs_dispatches_correctly(self):
        responses.add(
            responses.GET,
            "https://boards-api.greenhouse.io/v1/boards/testco/jobs?content=true",
            json={"jobs": [{"id": 1, "title": "Engineer", "content": "", "location": {"name": ""}, "departments": [], "absolute_url": "https://example.com", "updated_at": None}]},
            status=200,
        )

        client = ATSClient()
        jobs = client.fetch_jobs("greenhouse", "testco")
        assert len(jobs) == 1

    def test_fetch_jobs_unknown_platform(self):
        client = ATSClient()
        jobs = client.fetch_jobs("unknown_platform", "testco")
        assert jobs == []
