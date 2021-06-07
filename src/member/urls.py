from django.urls import include, path
from rest_framework.routers import DefaultRouter

from member import views

router = DefaultRouter()
router.register(r"", views.MemberViewSet, basename="member")
router.register("", views.UserIPViewSet, basename="userip")

urlpatterns = [path("self/", views.SelfView.as_view(), name="member-self"), path("", include(router.urls), name="member")]
