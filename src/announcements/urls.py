from django.urls import include, path
from rest_framework.routers import DefaultRouter

from announcements import views

router = DefaultRouter()
router.register("", views.AnnouncementViewSet, basename="announcements")
urlpatterns = [
    path("", include(router.urls)),
]
