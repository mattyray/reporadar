from django.urls import path

from . import views

urlpatterns = [
    path("", views.SearchCreateView.as_view(), name="search-create"),
    path("<uuid:id>/status/", views.SearchStatusView.as_view(), name="search-status"),
    path("<uuid:id>/results/", views.SearchResultsView.as_view(), name="search-results"),
    path("history/", views.SearchHistoryView.as_view(), name="search-history"),
    path("presets/", views.SearchPresetListCreateView.as_view(), name="search-presets"),
    path("company/", views.CompanyLookupView.as_view(), name="company-lookup"),
    path("company/scan/", views.CompanyScanView.as_view(), name="company-scan"),
    path("company/scan/status/", views.CompanyScanStatusView.as_view(), name="company-scan-status"),
]
