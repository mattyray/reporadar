"""Tests for analytics dashboard endpoint."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.analytics.models import AuthEvent, PageView, Session

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="user", email="user@example.com", password="userpass123"
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client


@pytest.fixture
def user_client(regular_user):
    client = APIClient()
    client.force_authenticate(regular_user)
    return client


@pytest.fixture
def sample_traffic(db):
    """Create some sessions and page views for testing."""
    sessions = []
    for i in range(3):
        s = Session.objects.create(
            visitor_hash=f"hash_{i}",
            ip_address=f"1.2.3.{i}",
            user_agent="Mozilla/5.0 Test Browser",
            device_type="desktop",
            browser="Chrome",
            os="macOS",
            is_bot=False,
            country="US" if i < 2 else "IN",
            referrer_domain="google.com" if i == 0 else "",
        )
        sessions.append(s)
        PageView.objects.create(session=s, path="/", page_title="Home")
        PageView.objects.create(session=s, path="/dashboard", page_title="Dashboard")

    # Add a bot session
    bot = Session.objects.create(
        visitor_hash="bot_hash",
        ip_address="10.0.0.1",
        user_agent="Googlebot",
        device_type="desktop",
        browser="Other",
        os="Other",
        is_bot=True,
    )
    PageView.objects.create(session=bot, path="/", page_title="Home")
    return sessions


@pytest.mark.django_db
class TestDashboardView:
    def test_admin_can_access(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["human_sessions"] == 3
        assert data["summary"]["bot_sessions"] == 1
        assert data["summary"]["page_views"] == 6  # 3 sessions x 2 pages

    def test_regular_user_forbidden(self, user_client):
        resp = user_client.get("/api/analytics/dashboard/")
        assert resp.status_code == 403

    def test_unauthenticated_forbidden(self):
        client = APIClient()
        resp = client.get("/api/analytics/dashboard/")
        assert resp.status_code in (401, 403)

    def test_top_pages(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        pages = resp.json()["top_pages"]
        paths = [p["path"] for p in pages]
        assert "/" in paths
        assert "/dashboard" in paths

    def test_countries(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        countries = resp.json()["countries"]
        codes = [c["country"] for c in countries]
        assert "US" in codes
        assert "IN" in codes

    def test_devices(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        devices = resp.json()["devices"]
        assert devices[0]["device_type"] == "desktop"
        assert devices[0]["count"] == 3

    def test_referrers(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        referrers = resp.json()["referrers"]
        assert len(referrers) == 1
        assert referrers[0]["referrer_domain"] == "google.com"

    def test_days_param(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["days"] == 7
        assert len(data["daily"]) > 0

    def test_funnel_data(self, admin_client, db):
        """Sessions that visit login + dashboard show up in funnel."""
        s = Session.objects.create(
            visitor_hash="funnel_test",
            ip_address="1.1.1.1",
            user_agent="Test",
            device_type="desktop",
            browser="Chrome",
            os="macOS",
            is_bot=False,
        )
        PageView.objects.create(session=s, path="/")
        PageView.objects.create(session=s, path="/login")
        PageView.objects.create(session=s, path="/auth/callback?token=abc")
        PageView.objects.create(session=s, path="/dashboard")

        resp = admin_client.get("/api/analytics/dashboard/")
        funnel = resp.json()["funnel"]
        assert funnel["landed"] == 1
        assert funnel["visited_login"] == 1
        assert funnel["completed_auth"] == 1
        assert funnel["reached_dashboard"] == 1

    def test_behavior_metrics(self, admin_client, sample_traffic):
        resp = admin_client.get("/api/analytics/dashboard/")
        behavior = resp.json()["behavior"]
        assert behavior["avg_pages_per_session"] == 2.0  # each session has 2 pages
        assert behavior["bounce_rate"] == 0  # no single-page sessions
        assert behavior["single_page_sessions"] == 0

    def test_auth_events(self, admin_client, db):
        AuthEvent.objects.create(
            provider="google", event="login_callback", outcome="success",
            user_email="user@test.com", ip_address="1.2.3.4",
        )
        AuthEvent.objects.create(
            provider="google", event="login_callback", outcome="error",
            ip_address="5.6.7.8", error_message="status=500",
        )
        resp = admin_client.get("/api/analytics/dashboard/")
        auth = resp.json()["auth"]
        assert auth["google_success"] == 1
        assert auth["google_error"] == 1
        assert len(auth["recent_errors"]) == 1
        assert auth["recent_errors"][0]["error_message"] == "status=500"

    def test_jwt_token_stripped_from_paths(self, admin_client, db):
        s = Session.objects.create(
            visitor_hash="jwt_test",
            ip_address="1.1.1.1",
            user_agent="Test",
            device_type="desktop",
            browser="Chrome",
            os="macOS",
            is_bot=False,
        )
        PageView.objects.create(
            session=s,
            path="/auth/callback?token=eyJhbGciOiJIUzI1NiJ9.longtoken",
        )
        resp = admin_client.get("/api/analytics/dashboard/")
        pages = resp.json()["top_pages"]
        for p in pages:
            assert "token=" not in p["path"]
            assert p["path"] == "/auth/callback"
