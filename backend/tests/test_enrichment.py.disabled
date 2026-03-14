"""Tests for enrichment views."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import APICredential
from apps.enrichment.models import EnrichmentLog, OrganizationContact
from apps.enrichment.views import _extract_domain, _is_eng_lead
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
        website="https://acme.com",
    )


@pytest.fixture
def hunter_key(user):
    return APICredential.objects.create(
        user=user,
        provider="hunter",
        encrypted_key="test-api-key",
        is_valid=True,
    )


# --- Unit tests for helper functions ---


def test_extract_domain_from_website():
    org = MagicMock()
    org.website = "https://acme.com/about"
    org.email = ""
    assert _extract_domain(org) == "acme.com"


def test_extract_domain_from_email():
    org = MagicMock()
    org.website = ""
    org.email = "info@acme.com"
    assert _extract_domain(org) == "acme.com"


def test_extract_domain_none():
    org = MagicMock()
    org.website = ""
    org.email = ""
    assert _extract_domain(org) is None


def test_is_eng_lead_positive():
    assert _is_eng_lead("VP of Engineering", "executive") is True
    assert _is_eng_lead("CTO", "c_level") is True
    assert _is_eng_lead("Engineering Manager", "manager") is True
    assert _is_eng_lead("Staff Engineer", "senior") is True
    assert _is_eng_lead("Tech Lead", "senior") is True


def test_is_eng_lead_negative():
    assert _is_eng_lead("Software Engineer", "junior") is False
    assert _is_eng_lead("Marketing Manager", "manager") is False
    assert _is_eng_lead("", "senior") is False
    assert _is_eng_lead(None, "senior") is False


# --- API endpoint tests ---


@pytest.mark.django_db
def test_enrich_no_hunter_key(api_client, org):
    response = api_client.post(f"/api/enrichment/{org.id}/enrich/")
    assert response.status_code == 400
    assert "Hunter" in response.data["detail"]


@pytest.mark.django_db
def test_enrich_no_domain(api_client, user, hunter_key):
    org = Organization.objects.create(
        github_login="no-website",
        github_id=99999,
        name="No Website Org",
    )
    response = api_client.post(f"/api/enrichment/{org.id}/enrich/")
    assert response.status_code == 400
    assert "domain" in response.data["detail"].lower()


@pytest.mark.django_db
def test_enrich_org_not_found(api_client):
    response = api_client.post("/api/enrichment/99999/enrich/")
    assert response.status_code == 404


@pytest.mark.django_db
@patch("apps.enrichment.views.HunterProvider")
def test_enrich_no_emails_found(mock_provider_cls, api_client, org, hunter_key):
    mock_provider = MagicMock()
    mock_provider.email_count.return_value = 0
    mock_provider_cls.return_value = mock_provider

    response = api_client.post(f"/api/enrichment/{org.id}/enrich/")
    assert response.status_code == 200
    assert response.data["contacts"] == []
    assert "no email data" in response.data["message"].lower()


@pytest.mark.django_db
def test_enrich_returns_cached_contacts(api_client, org, hunter_key):
    OrganizationContact.objects.create(
        organization=org,
        provider="hunter",
        first_name="Jane",
        last_name="Doe",
        email="jane@acme.com",
        source_domain="acme.com",
        last_enriched_at=timezone.now(),
    )
    response = api_client.post(f"/api/enrichment/{org.id}/enrich/")
    assert response.status_code == 200
    assert response.data["cached"] is True
    assert len(response.data["contacts"]) == 1


@pytest.mark.django_db
def test_contacts_list(api_client, org):
    OrganizationContact.objects.create(
        organization=org,
        provider="hunter",
        first_name="Jane",
        last_name="Doe",
        email="jane@acme.com",
        source_domain="acme.com",
        is_engineering_lead=True,
    )
    OrganizationContact.objects.create(
        organization=org,
        provider="hunter",
        first_name="John",
        last_name="Smith",
        email="john@acme.com",
        source_domain="acme.com",
        is_engineering_lead=False,
    )
    response = api_client.get(f"/api/enrichment/{org.id}/contacts/")
    assert response.status_code == 200
    assert len(response.data) == 2
    # Eng leads should be first
    assert response.data[0]["first_name"] == "Jane"
