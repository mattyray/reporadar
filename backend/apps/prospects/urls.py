from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProspectListView.as_view(), name="prospect-list"),
    path("<int:pk>/", views.ProspectDetailView.as_view(), name="prospect-detail"),
    path("<int:pk>/save/", views.SaveProspectView.as_view(), name="prospect-save"),
    path("saved/", views.SavedProspectListView.as_view(), name="prospect-saved-list"),
    path("saved/<int:pk>/", views.SavedProspectDeleteView.as_view(), name="prospect-saved-delete"),
    path("export/", views.ProspectExportView.as_view(), name="prospect-export"),
]
