from django.urls import include, path
from rest_framework.routers import DefaultRouter

from team import views

router = DefaultRouter()
router.register(r"", views.TeamViewSet, basename="team")

group_router = DefaultRouter()
group_router.register(r"", views.LeaderboardGroupViewSet, basename="groups")

urlpatterns = [
    path("self/", views.SelfView.as_view(), name="team-self"),
    path("create/", views.CreateTeamView.as_view(), name="team-create"),
    path("join/", views.JoinTeamView.as_view(), name="team-join"),
    path("leave/", views.LeaveTeamView.as_view(), name="team-leave"),
    path("groups/", include(group_router.urls), name="leaderboard-groups"),
    path("", include(router.urls), name="team"),
]
