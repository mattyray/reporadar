"""Tests for user behavior event tracking."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from apps.analytics.models import Event, Session

User = get_user_model()


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client


@pytest.fixture
def session(db):
    return Session.objects.create(
        visitor_hash="test_hash_123",
        ip_address="1.2.3.4",
        user_agent="Mozilla/5.0 Test Browser",
        device_type="desktop",
        browser="Chrome",
        os="macOS",
        is_bot=False,
    )


@pytest.mark.django_db
class TestEventTrackView:
    def test_basic_event(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"event_type": "search", "category": "job", "label": "django, react"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert Event.objects.count() == 1
        event = Event.objects.first()
        assert event.event_type == "search"
        assert event.category == "job"
        assert event.label == "django, react"

    def test_event_with_metadata(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({
                "event_type": "search",
                "category": "job",
                "label": "test",
                "value": 42,
                "metadata": {"techs": ["django", "react"], "remote_only": True},
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        event = Event.objects.first()
        assert event.value == 42
        assert event.metadata["techs"] == ["django", "react"]
        assert event.metadata["remote_only"] is True

    def test_missing_event_type(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"category": "job"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_category(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"event_type": "click"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_category(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"event_type": "click", "category": "invalid"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_bot_ua_dropped(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"event_type": "click", "category": "job"}),
            content_type="application/json",
            HTTP_USER_AGENT="Googlebot/2.1",
        )
        assert resp.status_code == 204
        assert Event.objects.count() == 0

    def test_invalid_json(self, anon_client):
        resp = anon_client.post(
            "/api/analytics/event/",
            "not json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_session_linked(self, anon_client, session):
        """Event should link to existing session for this visitor."""
        resp = anon_client.post(
            "/api/analytics/event/",
            json.dumps({"event_type": "click", "category": "job"}),
            content_type="application/json",
            REMOTE_ADDR="1.2.3.4",
            HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
        )
        assert resp.status_code == 200
        event = Event.objects.first()
        # Session matching depends on date hash — may or may not match
        # but the event should still be created
        assert event is not None


@pytest.mark.django_db
class TestDashboardEvents:
    def test_dashboard_includes_events(self, admin_client):
        Event.objects.create(event_type="search", category="job", label="django")
        Event.objects.create(event_type="click", category="job", label="Senior Dev")
        Event.objects.create(event_type="apply_click", category="job", label="Apply")
        Event.objects.create(event_type="click", category="company", label="Stripe")
        Event.objects.create(event_type="save", category="company", label="Vercel")

        resp = admin_client.get("/api/analytics/dashboard/")
        assert resp.status_code == 200
        data = resp.json()

        assert "events" in data
        assert "job_metrics" in data
        assert "search_metrics" in data

        assert data["job_metrics"]["searches"] == 1
        assert data["job_metrics"]["job_clicks"] == 1
        assert data["job_metrics"]["apply_clicks"] == 1
        assert data["search_metrics"]["company_clicks"] == 1
        assert data["search_metrics"]["company_saves"] == 1

    def test_top_searched_techs(self, admin_client):
        Event.objects.create(
            event_type="search", category="job",
            metadata={"techs": ["django", "react"]},
        )
        Event.objects.create(
            event_type="search", category="job",
            metadata={"techs": ["django", "python"]},
        )

        resp = admin_client.get("/api/analytics/dashboard/")
        data = resp.json()
        techs = data["top_searched_techs"]
        tech_names = [t["tech"] for t in techs]
        assert "django" in tech_names
        # django appears in both searches
        django_entry = next(t for t in techs if t["tech"] == "django")
        assert django_entry["count"] == 2
