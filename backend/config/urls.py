import json

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def dev_login(request):
    """Dev-only email/password login via Django session. Never available in production."""
    if not settings.DEBUG:
        return JsonResponse({"detail": "Not available"}, status=404)
    if request.method != "POST":
        return JsonResponse({"detail": "POST only"}, status=405)
    data = json.loads(request.body)
    user = authenticate(username=data.get("username", ""), password=data.get("password", ""))
    if not user:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    from django.contrib.auth import login
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"token": "session", "user": {"email": user.email}})


urlpatterns = [
    path("api/health/", lambda r: JsonResponse({"status": "ok"})),
    path("api/dev/login/", dev_login),
    path("admin/", admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/search/", include("apps.search.urls")),
    path("api/prospects/", include("apps.prospects.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/enrichment/", include("apps.enrichment.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/outreach/", include("apps.outreach.urls")),
]
