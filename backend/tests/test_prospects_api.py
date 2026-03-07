"""Tests for prospects API endpoints and CSV export."""

import csv
import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.prospects.models import (
    Organization,
    OrganizationRepo,
    RepoStackDetection,
    SavedProspect,
)

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
        location="San Francisco",
        github_url="https://github.com/acme-corp",
    )


@pytest.fixture
def org_with_stack(org):
    repo = OrganizationRepo.objects.create(
        organization=org,
        github_id=99999,
        name="main-app",
        full_name="acme-corp/main-app",
        url="https://github.com/acme-corp/main-app",
    )
    RepoStackDetection.objects.create(
        repo=repo, technology_name="Django", category="backend", source_file="requirements.txt"
    )
    RepoStackDetection.objects.create(
        repo=repo, technology_name="React", category="frontend", source_file="package.json"
    )
    return org


# --- Prospect List / Detail ---


@pytest.mark.django_db
def test_prospect_list(api_client, org):
    response = api_client.get("/api/prospects/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["github_login"] == "acme-corp"


@pytest.mark.django_db
def test_prospect_detail(api_client, org_with_stack):
    response = api_client.get(f"/api/prospects/{org_with_stack.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "Acme Corporation"
    assert len(response.data["repos"]) == 1
    assert len(response.data["repos"][0]["stack_detections"]) == 2


# --- Save / Unsave ---


@pytest.mark.django_db
def test_save_prospect(api_client, org, user):
    response = api_client.post(f"/api/prospects/{org.id}/save/", {"notes": "Great fit"})
    assert response.status_code == 201
    assert SavedProspect.objects.filter(user=user, organization=org).exists()


@pytest.mark.django_db
def test_save_prospect_duplicate(api_client, org, user):
    SavedProspect.objects.create(user=user, organization=org)
    response = api_client.post(f"/api/prospects/{org.id}/save/")
    assert response.status_code == 409


@pytest.mark.django_db
def test_saved_prospect_list(api_client, org, user):
    SavedProspect.objects.create(user=user, organization=org, notes="Test")
    response = api_client.get("/api/prospects/saved/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_delete_saved_prospect(api_client, org, user):
    sp = SavedProspect.objects.create(user=user, organization=org)
    response = api_client.delete(f"/api/prospects/saved/{sp.id}/")
    assert response.status_code == 204
    assert not SavedProspect.objects.filter(id=sp.id).exists()


@pytest.mark.django_db
def test_prospect_not_found(api_client):
    response = api_client.post("/api/prospects/99999/save/")
    assert response.status_code == 404


# --- CSV Export ---


@pytest.mark.django_db
def test_csv_export_empty(api_client):
    response = api_client.get("/api/prospects/export/")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    content = response.content.decode()
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1  # header only


@pytest.mark.django_db
def test_csv_export_with_data(api_client, org_with_stack, user):
    SavedProspect.objects.create(user=user, organization=org_with_stack, notes="Top pick", status="researched")

    response = api_client.get("/api/prospects/export/")
    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]

    content = response.content.decode()
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    assert len(rows) == 2  # header + 1 data row
    header = rows[0]
    data = rows[1]

    assert "Organization" in header
    assert "Tech Stack" in header

    # Check data values
    assert data[0] == "Acme Corporation"
    assert data[1] == "https://github.com/acme-corp"
    assert data[5] == "researched"
    assert data[6] == "Top pick"
    assert "Django" in data[7]
    assert "React" in data[7]


@pytest.mark.django_db
def test_csv_export_only_own_prospects(api_client, org, user):
    other_user = User.objects.create_user(
        username="other", email="other@example.com", password="pass123"
    )
    SavedProspect.objects.create(user=other_user, organization=org)

    response = api_client.get("/api/prospects/export/")
    content = response.content.decode()
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1  # header only — other user's data not included
