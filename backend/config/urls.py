from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/search/", include("apps.search.urls")),
    path("api/prospects/", include("apps.prospects.urls")),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/enrichment/", include("apps.enrichment.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/outreach/", include("apps.outreach.urls")),
]
