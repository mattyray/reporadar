from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.ResumeUploadView.as_view(), name="resume-upload"),
    path("profile/", views.ResumeProfileView.as_view(), name="resume-profile"),
    path("matched-jobs/", views.MatchedJobsView.as_view(), name="matched-jobs"),
]
