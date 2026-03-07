from django.urls import path

from . import views

urlpatterns = [
    path("<int:org_id>/enrich/", views.EnrichOrganizationView.as_view(), name="enrich-org"),
    path("<int:org_id>/contacts/", views.OrganizationContactsView.as_view(), name="org-contacts"),
]
