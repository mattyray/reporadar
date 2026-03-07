from django.urls import path

from . import views

urlpatterns = [
    path("", views.JobSearchView.as_view(), name="job-search"),
    path("org/<int:org_id>/", views.OrgJobsView.as_view(), name="org-jobs"),
    path("org/<int:org_id>/check/", views.OrgJobsCheckView.as_view(), name="org-jobs-check"),
]
