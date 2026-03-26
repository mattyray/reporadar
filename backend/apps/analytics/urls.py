from django.urls import path

from .views import DashboardView, EventTrackView, StatsView, TrackView

urlpatterns = [
    path("track/", TrackView.as_view(), name="analytics-track"),
    path("event/", EventTrackView.as_view(), name="analytics-event"),
    path("stats/", StatsView.as_view(), name="analytics-stats"),
    path("dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
]
