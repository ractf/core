"""URL routes for the member app."""

from django.urls import include, path
from member import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"", views.MemberViewSet, basename="member")
router.register("", views.UserIPViewSet, basename="userip")

urlpatterns = [
    path("self/", views.SelfView.as_view(), name="member-self"),
    path("", include(router.urls), name="member"),
]
