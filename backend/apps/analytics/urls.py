from django.urls import path

from .views import StatsView, TrackView

urlpatterns = [
    path("track/", TrackView.as_view(), name="analytics-track"),
    path("stats/", StatsView.as_view(), name="analytics-stats"),
]
