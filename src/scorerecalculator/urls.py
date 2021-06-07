from django.urls import path

from scorerecalculator import views

urlpatterns = [
    path("team/<int:id>/", views.RecalculateTeamView.as_view(), name="recalculate-team"),
    path("user/<int:id>/", views.RecalculateUserView.as_view(), name="recalculate-user"),
    path("", views.RecalculateAllView.as_view(), name="recalculate-all"),
]
