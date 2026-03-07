"""Tests for Hunter.io API adapter with mocked responses."""

import json
from pathlib import Path

import responses

from providers.hunter import HUNTER_API_BASE, HunterProvider

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@responses.activate
def test_email_count():
    responses.add(
        responses.GET,
        f"{HUNTER_API_BASE}/email-count",
        json={"data": {"total": 47, "personal_emails": 35, "generic_emails": 12}},
        status=200,
    )

    provider = HunterProvider()
    count = provider.email_count("test-api-key", "acme.com")

    assert count == 47
    # Verify the API key was sent as a query param
    assert "api_key=test-api-key" in responses.calls[0].request.url


@responses.activate
def test_domain_search():
    fixture = load_fixture("hunter_domain_search_response.json")
    responses.add(
        responses.GET,
        f"{HUNTER_API_BASE}/domain-search",
        json=fixture,
        status=200,
    )

    provider = HunterProvider()
    result = provider.domain_search("test-api-key", "acme.com")

    assert result.domain == "acme.com"
    assert result.organization == "Acme Corporation"
    assert result.total_emails == 3
    assert len(result.contacts) == 3

    # Check first contact
    jane = result.contacts[0]
    assert jane.first_name == "Jane"
    assert jane.last_name == "Doe"
    assert jane.email == "jane.doe@acme.com"
    assert jane.confidence == 95
    assert jane.position == "VP of Engineering"
    assert jane.seniority == "executive"
    assert jane.department == "engineering"
    assert jane.linkedin_url == "https://linkedin.com/in/janedoe"


@responses.activate
def test_domain_search_with_department_filter():
    responses.add(
        responses.GET,
        f"{HUNTER_API_BASE}/domain-search",
        json={"data": {"domain": "acme.com", "organization": "Acme", "total": 0, "emails": []}},
        status=200,
    )

    provider = HunterProvider()
    provider.domain_search("test-api-key", "acme.com", department="engineering")

    assert "department=engineering" in responses.calls[0].request.url


@responses.activate
def test_find_email():
    responses.add(
        responses.GET,
        f"{HUNTER_API_BASE}/email-finder",
        json={
            "data": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@acme.com",
                "confidence": 96,
            }
        },
        status=200,
    )

    provider = HunterProvider()
    result = provider.find_email("test-api-key", "acme.com", "Jane", "Doe")

    assert result.email == "jane.doe@acme.com"
    assert result.confidence == 96
    assert result.first_name == "Jane"
    assert result.last_name == "Doe"


@responses.activate
def test_check_credits():
    responses.add(
        responses.GET,
        f"{HUNTER_API_BASE}/account",
        json={
            "data": {
                "requests": {
                    "searches": {"available": 50, "used": 12}
                }
            }
        },
        status=200,
    )

    provider = HunterProvider()
    credits = provider.check_credits("test-api-key")

    assert credits["total"] == 50
    assert credits["used"] == 12
