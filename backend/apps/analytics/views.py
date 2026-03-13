import logging
from datetime import date

import requests as http_requests
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import PageView, Session

logger = logging.getLogger(__name__)

BOT_UA_PATTERNS = [
    "bot", "crawl", "spider", "slurp", "phantom", "puppet",
    "selenium", "playwright", "headlesschrome", "wget", "curl",
]


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def parse_user_agent(ua_string: str) -> dict:
    """Simple UA parsing without external dependency."""
    ua_lower = ua_string.lower()

    # Device type
    if any(m in ua_lower for m in ["mobile", "android", "iphone", "ipod"]):
        device_type = "mobile"
    elif any(t in ua_lower for t in ["tablet", "ipad"]):
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Browser
    if "firefox" in ua_lower:
        browser = "Firefox"
    elif "edg" in ua_lower:
        browser = "Edge"
    elif "chrome" in ua_lower or "chromium" in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower:
        browser = "Safari"
    else:
        browser = "Other"

    # OS
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
    else:
        os_name = "Other"

    return {"device_type": device_type, "browser": browser, "os": os_name}


def geoip_lookup(ip: str) -> dict:
    """Look up country/region/city from IP using ip-api.com (free, no key, 45 req/min)."""
    try:
        resp = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=country,regionName,city",
            timeout=2,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "country": data.get("country", ""),
                "region": data.get("regionName", ""),
                "city": data.get("city", ""),
            }
    except Exception:
        pass
    return {"country": "", "region": "", "city": ""}


def detect_bot(ua_string: str, has_accept_language: bool) -> bool:
    ua_lower = ua_string.lower()
    if any(p in ua_lower for p in BOT_UA_PATTERNS):
        return True
    if not has_accept_language:
        return True
    return False


@method_decorator(csrf_exempt, name="dispatch")
class TrackView(View):
    """POST /api/analytics/track/ — record page views, no auth required."""

    def post(self, request):
        import json

        try:
            # sendBeacon sends as text/plain, so we parse the body regardless of content-type
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # If this is a time-on-page update for an existing page view
        page_view_id = data.get("page_view_id")
        time_on_page = data.get("time_on_page")
        if page_view_id and time_on_page is not None:
            try:
                pv = PageView.objects.get(id=page_view_id)
                pv.time_on_page_seconds = float(time_on_page)
                pv.save(update_fields=["time_on_page_seconds"])
                return JsonResponse({"ok": True})
            except PageView.DoesNotExist:
                return JsonResponse({"error": "Not found"}, status=404)

        # New page view
        path = data.get("path", "")
        if not path:
            return JsonResponse({"error": "path required"}, status=400)

        ip = get_client_ip(request)
        ua_string = request.META.get("HTTP_USER_AGENT", "")
        today = date.today().isoformat()

        session_hash = Session.make_hash(ip, ua_string, today)
        ua_info = parse_user_agent(ua_string)
        is_bot = detect_bot(ua_string, bool(request.META.get("HTTP_ACCEPT_LANGUAGE")))

        geo = geoip_lookup(ip) if not is_bot else {"country": "", "region": "", "city": ""}

        session, created = Session.objects.get_or_create(
            session_hash=session_hash,
            defaults={
                "ip_address": ip,
                "user_agent": ua_string,
                "device_type": ua_info["device_type"],
                "browser": ua_info["browser"],
                "os": ua_info["os"],
                "is_bot": is_bot,
                "country": geo["country"],
                "region": geo["region"],
                "city": geo["city"],
                "referrer": data.get("referrer", "")[:200],
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
