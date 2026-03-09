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


def oauth_callback(request):
    """Handle Google OAuth callback: let allauth process it, then redirect
    to the frontend with a JWT token in the URL fragment.

    The session cookie is on Railway's domain and can't be read by the
    Netlify frontend, so we generate a JWT and pass it via URL."""
    from urllib.parse import urlencode

    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
    from django.shortcuts import redirect

    # Let allauth handle the OAuth callback (token exchange, user creation)
    view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
    response = view(request)

    # If allauth succeeded (302 redirect) and user is now authenticated,
    # generate a JWT and redirect to frontend with it
    if response.status_code == 302 and request.user.is_authenticated:
        from allauth.headless.tokens.strategies.jwt.strategy import JWTTokenStrategy

        strategy = JWTTokenStrategy()
        token_data = strategy.create_access_token(request)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        # Pass token as query param — frontend will grab it and store in localStorage
        callback_url = f"{frontend_url}/auth/callback?{urlencode({'token': token_data})}"
        return redirect(callback_url)

    # If allauth didn't succeed, return its response as-is (error page)
    return response


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
    path("accounts/google/login/callback/", oauth_callback),
    path("accounts/", include("allauth.urls")),  # Other allauth views
    path("api/search/", include("apps.search.urls")),
    path("api/prospects/", include("apps.prospects.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/enrichment/", include("apps.enrichment.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/outreach/", include("apps.outreach.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
]
