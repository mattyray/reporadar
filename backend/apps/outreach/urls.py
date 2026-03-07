from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.OutreachGenerateView.as_view(), name="outreach-generate"),
    path("history/", views.OutreachHistoryView.as_view(), name="outreach-history"),
]
