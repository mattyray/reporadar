"""Tests for public stats endpoint."""

import pytest
from django.test import Client

from apps.jobs.models import JobListing


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_stats_endpoint_returns_counts(client):
    from django.core.cache import cache
    cache.clear()

    # Create a couple active jobs
    JobListing.objects.create(
        source="remoteok",
        company_name="Acme",
        external_id="rok-1",
        title="Django Dev",
        apply_url="https://example.com/1",
        detected_techs=["Django", "Python"],
    )
    JobListing.objects.create(
        source="remotive",
        company_name="Beta Co",
        external_id="rem-1",
        title="React Dev",
        apply_url="https://example.com/2",
        detected_techs=["React"],
    )

    response = client.get("/api/analytics/stats/")
    assert response.status_code == 200
    data = response.json()
    assert data["active_jobs"] == 2
    assert data["tech_count"] == 3  # django, python, react


@pytest.mark.django_db
def test_stats_endpoint_no_auth_required(client):
    from django.core.cache import cache
    cache.clear()

    response = client.get("/api/analytics/stats/")
    assert response.status_code == 200
    assert response.json()["active_jobs"] == 0
