"""URL routes for the config app."""

from django.urls import path

from config import views

urlpatterns = [
    path("", views.ConfigView.as_view(), name="config-list"),
    path("<str:name>/", views.ConfigView.as_view(), name="config-pk"),
]
