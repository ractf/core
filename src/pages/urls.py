"""URL routes for the pages app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from pages import views

router = DefaultRouter()
router.register(r"", views.TagViewSet, basename="pages")

urlpatterns = [path("", include(router.urls))]
