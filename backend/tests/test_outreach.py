"""Tests for outreach message generation."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.enrichment.models import OrganizationContact
from apps.outreach.models import OutreachMessage
from apps.outreach.views import _build_prompt
from apps.prospects.models import Organization, OrganizationRepo, RepoStackDetection
from apps.resumes.models import ResumeProfile

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
        description="Building cool stuff with Django",
        website="https://acme.com",
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


@pytest.fixture
def resume(user):
    return ResumeProfile.objects.create(
        user=user,
        original_file="resumes/test.pdf",
        file_type="pdf",
        summary="Full-stack developer with 5 years Django experience.",
        tech_stack=["Django", "Python", "React", "TypeScript"],
        key_projects=[{"name": "RepoRadar", "description": "GitHub prospect finder", "tech": ["Django"]}],
        story_hook="Self-taught dev who transitioned from teaching.",
    )


# --- Unit tests for prompt builder ---


def test_build_prompt_includes_user_profile():
    context = {
        "message_type": "email",
        "organization": {"name": "Acme", "description": "Tech co", "stack": ["Django"]},
        "contact": {"name": "Jane Doe", "position": "CTO"},
        "user_profile": {
            "summary": "Django dev",
            "tech_stack": ["Django", "React"],
            "key_projects": "Built RepoRadar",
            "story_hook": "Self-taught",
        },
    }
    prompt = _build_prompt(context)
    assert "Django dev" in prompt
    assert "Acme" in prompt
    assert "Jane Doe" in prompt
    assert "Self-taught" in prompt


def test_build_prompt_linkedin_dm_length_guide():
    context = {
        "message_type": "linkedin_dm",
        "organization": {"name": "Co", "description": "", "stack": []},
        "contact": {"name": "", "position": ""},
        "user_profile": {"summary": "", "tech_stack": [], "key_projects": "", "story_hook": ""},
    }
    prompt = _build_prompt(context)
    assert "300 characters" in prompt


def test_build_prompt_email_length_guide():
    context = {
        "message_type": "email",
        "organization": {"name": "Co", "description": "", "stack": []},
        "contact": {"name": "", "position": ""},
        "user_profile": {"summary": "", "tech_stack": [], "key_projects": "", "story_hook": ""},
    }
    prompt = _build_prompt(context)
    assert "3-4 short paragraphs" in prompt


# --- API endpoint tests ---


@pytest.mark.django_db
@patch("apps.outreach.views.anthropic")
def test_generate_outreach_success(mock_anthropic, api_client, org_with_stack, resume):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Hi Jane, I noticed Acme uses Django...")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.Anthropic.return_value = mock_client

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        response = api_client.post("/api/outreach/generate/", {
            "organization_id": org_with_stack.id,
            "message_type": "email",
        })

    assert response.status_code == 201
    assert "Hi Jane" in response.data["body"]
    assert OutreachMessage.objects.count() == 1


@pytest.mark.django_db
def test_generate_outreach_requires_resume(api_client, org):
    response = api_client.post("/api/outreach/generate/", {
        "organization_id": org.id,
        "message_type": "email",
    })
    assert response.status_code == 400
    assert "resume" in response.data["detail"].lower()


@pytest.mark.django_db
def test_generate_outreach_org_not_found(api_client, resume):
    response = api_client.post("/api/outreach/generate/", {
        "organization_id": 99999,
        "message_type": "email",
    })
    assert response.status_code == 404


@pytest.mark.django_db
def test_outreach_history_returns_user_messages(api_client, user, org):
    OutreachMessage.objects.create(
        user=user,
        organization=org,
        message_type="email",
        body="Test message",
    )
    response = api_client.get("/api/outreach/history/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["body"] == "Test message"
