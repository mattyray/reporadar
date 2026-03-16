import json
import logging
from datetime import date, timedelta
from urllib.parse import urlparse

from django.core.cache import cache
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuthEvent, PageView, Session

logger = logging.getLogger(__name__)

# --- Bot UA patterns (silently dropped, never stored) ---
BOT_UA_PATTERNS = [
    "bot", "crawl", "spider", "slurp", "phantom", "puppet",
    "selenium", "playwright", "headlesschrome", "wget", "curl",
    "python-requests", "python-urllib", "aiohttp", "httpx",
    "go-http-client", "java/", "okhttp",
    "facebookexternalhit", "twitterbot", "linkedinbot",
    "whatsapp", "telegrambot", "discordbot",
    "googleother", "bingpreview", "yandex",
]

# --- Known data center cities (heuristic bot flag, stored with is_bot=True) ---
DATA_CENTER_CITIES = {
    "ashburn", "boydton", "boardman", "council bluffs",
    "the dalles", "dublin", "frankfurt am main", "singapore",
    "mumbai", "sao paulo", "tokyo", "sydney", "london",
    "paris", "amsterdam", "seoul", "montreal",
}

MAX_TIME_ON_PAGE = 3600  # Cap at 1 hour to prevent garbage data


def _get_client_ip(request):
    """Read X-Forwarded-For first (Railway is behind a proxy), fall back to REMOTE_ADDR."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _detect_device(ua_lower: str) -> str:
    if any(t in ua_lower for t in ["ipad", "tablet", "kindle"]):
        return "tablet"
    if any(m in ua_lower for m in ["iphone", "android", "mobile"]):
        return "mobile"
    return "desktop"


def _detect_browser(ua_lower: str) -> str:
    # Order matters: Edge contains "Chrome" and "Edg"
    if "edg" in ua_lower:
        return "Edge"
    if "firefox" in ua_lower:
        return "Firefox"
    if "chrome" in ua_lower or "chromium" in ua_lower:
        return "Chrome"
    if "safari" in ua_lower:
        return "Safari"
    return "Other"


def _detect_os(ua_lower: str) -> str:
    if "windows" in ua_lower:
        return "Windows"
    if "mac os" in ua_lower or "macintosh" in ua_lower:
        return "macOS"
    if "iphone" in ua_lower or "ipad" in ua_lower:
        return "iOS"
    if "android" in ua_lower:
        return "Android"
    if "linux" in ua_lower:
        return "Linux"
    return "Other"


def _extract_domain(url: str) -> str:
    """Pull netloc from referrer URL for grouping."""
    if not url:
        return ""
    try:
        return urlparse(url).netloc[:253]
    except Exception:
        return ""


def _get_geo(ip: str) -> dict:
    """GeoIP lookup. Tries MaxMind GeoLite2 first, falls back to ip-api.com."""
    # Try MaxMind first (fast, local, no rate limit)
    try:
        import geoip2.database

        reader = geoip2.database.Reader("/app/GeoLite2-City.mmdb")
        resp = reader.city(ip)
        return {
            "country": resp.country.iso_code or "",
            "region": resp.subdivisions.most_specific.name or "" if resp.subdivisions else "",
            "city": resp.city.name or "" if resp.city else "",
        }
    except Exception:
        pass

    # Fallback to ip-api.com (free, 45 req/min)
    try:
        import requests as http_requests

        resp = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=countryCode,regionName,city",
            timeout=2,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "country": data.get("countryCode", ""),
                "region": data.get("regionName", ""),
                "city": data.get("city", ""),
            }
    except Exception:
        pass

    return {"country": "", "region": "", "city": ""}


def _is_ua_bot(ua_string: str) -> bool:
    """Hard bot filter — matches get dropped entirely (204, nothing stored)."""
    ua_lower = ua_string.lower()
    return any(p in ua_lower for p in BOT_UA_PATTERNS)


def _is_heuristic_bot(has_accept_language: bool, city: str) -> bool:
    """Soft bot filter — stored with is_bot=True for review."""
    if not has_accept_language:
        return True
    if city and city.lower() in DATA_CENTER_CITIES:
        return True
    return False


@method_decorator(csrf_exempt, name="dispatch")
class TrackView(View):
    """POST /api/analytics/track/ — record page views, no auth required."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # --- Handle "leave" events (time-on-page update) ---
        event_type = data.get("type", "view")
        page_view_id = data.get("page_view_id")
        time_on_page = data.get("time_on_page")

        if event_type == "leave" and page_view_id and time_on_page is not None:
            ip = _get_client_ip(request)
            ua_string = request.META.get("HTTP_USER_AGENT", "")
            today = date.today().isoformat()
            visitor_hash = Session.make_hash(ip, ua_string, today)

            # Verify the page_view_id belongs to this visitor's session
            try:
                pv = PageView.objects.select_related("session").get(id=page_view_id)
                if pv.session.visitor_hash != visitor_hash:
                    return JsonResponse({"status": "ignored"}, status=204)
                pv.time_on_page_seconds = min(float(time_on_page), MAX_TIME_ON_PAGE)
                pv.save(update_fields=["time_on_page_seconds"])
                return JsonResponse({"ok": True})
            except (PageView.DoesNotExist, ValueError):
                return JsonResponse({"status": "not_found"}, status=204)

        # --- New page view ---
        path = data.get("path", "")
        if not path or len(path) > 500:
            return JsonResponse({"status": "ignored"}, status=204)

        ua_string = request.META.get("HTTP_USER_AGENT", "")

        # Tier 1: Hard UA bot filter — silently drop
        if _is_ua_bot(ua_string):
            return JsonResponse({"status": "ok"}, status=204)

        ip = _get_client_ip(request)
        today = date.today().isoformat()
        visitor_hash = Session.make_hash(ip, ua_string, today)

        # GeoIP lookup
        geo = _get_geo(ip)

        # Tier 2: Heuristic bot detection — store but flag
        has_accept_language = bool(request.META.get("HTTP_ACCEPT_LANGUAGE"))
        is_bot = _is_heuristic_bot(has_accept_language, geo.get("city", ""))

        ua_lower = ua_string.lower()
        referrer = data.get("referrer", "")[:200]

        session, created = Session.objects.get_or_create(
            visitor_hash=visitor_hash,
            defaults={
                "ip_address": ip,
                "user_agent": ua_string,
                "device_type": _detect_device(ua_lower),
                "browser": _detect_browser(ua_lower),
                "os": _detect_os(ua_lower),
                "is_bot": is_bot,
                "country": geo["country"],
                "region": geo["region"],
                "city": geo["city"],
                "referrer": referrer,
                "referrer_domain": _extract_domain(referrer),
                "screen_width": data.get("screen_width"),
                "screen_height": data.get("screen_height"),
                "utm_source": data.get("utm_source", "")[:200],
                "utm_medium": data.get("utm_medium", "")[:200],
                "utm_campaign": data.get("utm_campaign", "")[:200],
            },
        )

        if not created:
            session.save(update_fields=["last_seen_at"])

        pv = PageView.objects.create(
            session=session,
            path=path[:500],
            page_title=data.get("title", "")[:300],
            referrer_path=data.get("referrer_path", "")[:500],
        )

        return JsonResponse({"page_view_id": pv.id})


class StatsView(View):
    """GET /api/analytics/stats/ — public stats for landing page (cached 1hr)."""

    def get(self, request):
        stats = cache.get("public_stats")
        if stats:
            return JsonResponse(stats)

        from apps.jobs.models import JobListing
        from apps.prospects.models import Organization

        stats = {
            "active_jobs": JobListing.objects.filter(is_active=True).count(),
            "companies": Organization.objects.count(),
        }
        # Count unique techs across all active jobs
        raw_techs = (
            JobListing.objects.filter(is_active=True)
            .exclude(detected_techs=[])
            .values_list("detected_techs", flat=True)
        )
        unique_techs = set()
        for techs_list in raw_techs:
            if techs_list:
                unique_techs.update(t.lower() for t in techs_list)
        stats["tech_count"] = len(unique_techs)

        cache.set("public_stats", stats, 3600)
        return JsonResponse(stats)


class DashboardView(APIView):
    """GET /api/analytics/dashboard/ — traffic dashboard for admins.

    Query params:
        days: number of days to look back (default 1 = today)
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        days = min(int(request.query_params.get("days", 1)), 90)
        cutoff = timezone.now() - timedelta(days=days)
        human = Q(is_bot=False)

        sessions = Session.objects.filter(started_at__gte=cutoff)
        human_sessions = sessions.filter(human)
        page_views = PageView.objects.filter(
            viewed_at__gte=cutoff, session__is_bot=False
        )

        # -- Summary --
        summary = {
            "human_sessions": human_sessions.count(),
            "bot_sessions": sessions.filter(is_bot=True).count(),
            "page_views": page_views.count(),
            "days": days,
        }

        # -- Top pages --
        top_pages = list(
            page_views.values("path")
            .annotate(views=Count("id"))
            .order_by("-views")[:15]
        )
        # Strip JWT tokens from auth/callback paths for readability
        for p in top_pages:
            if "?" in p["path"]:
                p["path"] = p["path"].split("?")[0]
        # Re-aggregate after stripping query params
        merged = {}
        for p in top_pages:
            merged[p["path"]] = merged.get(p["path"], 0) + p["views"]
        top_pages = [
            {"path": k, "views": v}
            for k, v in sorted(merged.items(), key=lambda x: -x[1])
        ]

        # -- Devices --
        devices = list(
            human_sessions.values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # -- Browsers --
        browsers = list(
            human_sessions.values("browser")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # -- Countries --
        countries = list(
            human_sessions.exclude(country="")
            .values("country")
            .annotate(count=Count("id"))
            .order_by("-count")[:15]
        )

        # -- Referrers --
        referrers = list(
            human_sessions.exclude(referrer_domain="")
            .values("referrer_domain")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # -- Daily breakdown (when days > 1) --
        daily = []
        if days > 1:
            from django.db.models.functions import TruncDate

            daily = list(
                human_sessions.annotate(day=TruncDate("started_at"))
                .values("day")
                .annotate(sessions=Count("id"))
                .order_by("day")
            )
            for d in daily:
                d["day"] = d["day"].isoformat()

        # -- Auth events --
        auth_events = AuthEvent.objects.filter(created_at__gte=cutoff)
        auth = {
            "google_success": auth_events.filter(
                provider="google", outcome="success"
            ).count(),
            "google_error": auth_events.filter(
                provider="google", outcome="error"
            ).count(),
            "github_success": auth_events.filter(
                provider="github", outcome="success"
            ).count(),
            "github_error": auth_events.filter(
                provider="github", outcome="error"
            ).count(),
            "recent_errors": list(
                auth_events.filter(outcome="error")
                .order_by("-created_at")
                .values("provider", "event", "error_message", "ip_address", "created_at")[:10]
            ),
        }
        for e in auth["recent_errors"]:
            e["created_at"] = e["created_at"].isoformat()

        # -- Funnel (user behavior) --
        paths_by_session = {}
        for pv in page_views.values("session_id", "path"):
            paths_by_session.setdefault(pv["session_id"], set()).add(
                pv["path"].split("?")[0]
            )
        total = len(paths_by_session) or 1
        funnel = {
            "landed": len(paths_by_session),
            "visited_login": sum(
                1 for ps in paths_by_session.values() if "/login" in ps
            ),
            "completed_auth": sum(
                1 for ps in paths_by_session.values() if "/auth/callback" in ps
            ),
            "reached_dashboard": sum(
                1 for ps in paths_by_session.values()
                if "/dashboard" in ps or "/companies" in ps
            ),
            "viewed_company": sum(
                1 for ps in paths_by_session.values()
                if any(p.startswith("/prospects/") for p in ps)
            ),
            "visited_settings": sum(
                1 for ps in paths_by_session.values() if "/settings" in ps
            ),
        }

        # -- Session depth --
        pv_counts = list(
            page_views.values("session_id").annotate(c=Count("id")).values_list("c", flat=True)
        )
        bounce = sum(1 for c in pv_counts if c == 1)
        behavior = {
            "avg_pages_per_session": round(sum(pv_counts) / len(pv_counts), 1) if pv_counts else 0,
            "bounce_rate": round(bounce / len(pv_counts) * 100, 1) if pv_counts else 0,
            "single_page_sessions": bounce,
        }

        return Response(
            {
                "summary": summary,
                "top_pages": top_pages,
                "devices": devices,
                "browsers": browsers,
                "countries": countries,
                "referrers": referrers,
                "daily": daily,
                "auth": auth,
                "funnel": funnel,
                "behavior": behavior,
            }
        )
