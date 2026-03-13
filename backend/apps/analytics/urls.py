from django.urls import path

from .views import TrackView

urlpatterns = [
    path("track/", TrackView.as_view(), name="analytics-track"),
]
