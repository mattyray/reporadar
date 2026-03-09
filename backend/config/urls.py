import json
import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("config.urls")


@csrf_exempt
def oauth_start(request):
    """Start OAuth flow — redirects browser to the provider (Google).
    CSRF-exempt because this only initiates a redirect, no state is modified.
    The actual auth happens via the provider's callback with proper state verification."""
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
    from django.middleware.csrf import get_token

    # Set CSRF cookie for the callback
    get_token(request)
    # Delegate to allauth's OAuth2 login view
    view = OAuth2LoginView.adapter_view(GoogleOAuth2Adapter)
    return view(request)


def oauth_debug_callback(request):
    """Wrapper around allauth's Google OAuth callback that logs diagnostic info."""
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView

    logger.error("=== OAuth Callback Debug ===")
    logger.error(f"Full URL: {request.build_absolute_uri()}")
    logger.error(f"Scheme: {request.scheme}")
    logger.error(f"Host: {request.get_host()}")
    logger.error(f"META HTTP_X_FORWARDED_PROTO: {request.META.get('HTTP_X_FORWARDED_PROTO', 'NOT SET')}")
    logger.error(f"META HTTP_X_FORWARDED_HOST: {request.META.get('HTTP_X_FORWARDED_HOST', 'NOT SET')}")
    logger.error(f"Session key: {request.session.session_key}")
    logger.error(f"Session data keys: {list(request.session.keys())}")
    logger.error(f"Cookies: {list(request.COOKIES.keys())}")
    logger.error(f"Query params: {dict(request.GET)}")

    try:
        view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
        response = view(request)
        logger.error(f"Callback response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"OAuth callback exception: {type(e).__name__}: {e}", exc_info=True)
        raise


@csrf_exempt
def dev_login(request):
    """Dev-only email/password login via Django session. Never available in production."""
    if not settings.DEBUG:
        return JsonResponse({"detail": "Not available"}, status=404)
    if request.method != "POST":
        return JsonResponse({"detail": "POST only"}, status=405)
    data = json.loads(request.body)
    email = data.get("email", "")
    password = data.get("password", "")
    # Look up by email (our primary identifier), then authenticate with Django's username
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user_obj = User.objects.get(email=email)
        user = authenticate(username=user_obj.username, password=password)
    except User.DoesNotExist:
        user = None
    if not user:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    from django.contrib.auth import login
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"token": "session", "user": {"email": user.email}})


urlpatterns = [
    path("api/health/", lambda r: JsonResponse({"status": "ok"})),
    path("api/dev/login/", dev_login),
    path("api/auth/google/start/", oauth_start),
    path("admin/", admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/google/login/callback/", oauth_debug_callback),  # Debug wrapper
    path("accounts/", include("allauth.urls")),  # Other allauth views
    path("api/search/", include("apps.search.urls")),
    path("api/prospects/", include("apps.prospects.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/enrichment/", include("apps.enrichment.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/outreach/", include("apps.outreach.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
]
