from django.urls import path, include
from rest_framework.routers import DefaultRouter

from pages import views

router = DefaultRouter()
router.register(r"", views.TagViewSet, basename="pages")

urlpatterns = [path("", include(router.urls))]
