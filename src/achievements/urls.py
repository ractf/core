from django.urls import path, include
from rest_framework.routers import DefaultRouter

from achievements import views

router = DefaultRouter()
router.register("", views.AchievementViewSet, basename="achievements")
urlpatterns = [
    path("", include(router.urls)),
]
