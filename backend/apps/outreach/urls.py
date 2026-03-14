from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.OutreachGenerateView.as_view(), name="outreach-generate"),
    path("<uuid:pk>/status/", views.OutreachStatusView.as_view(), name="outreach-status"),
    path("history/", views.OutreachHistoryView.as_view(), name="outreach-history"),
]
