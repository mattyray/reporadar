from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.UserProfileView.as_view(), name="user-profile"),
    path("api-keys/", views.APIKeyListCreateView.as_view(), name="api-keys"),
    path("api-keys/status/", views.APIKeyStatusView.as_view(), name="api-keys-status"),
    path("api-keys/<str:provider>/", views.APIKeyDeleteView.as_view(), name="api-keys-delete"),
]
