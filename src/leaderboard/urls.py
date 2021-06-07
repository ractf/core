from django.urls import include, path
from rest_framework.routers import DefaultRouter

from leaderboard import views

router = DefaultRouter()
router.register("matrix/", views.MatrixScoreboardView, basename="leaderboard-matrix")

urlpatterns = [
    path("ctftime/", views.CTFTimeListView.as_view(), name="leaderboard-ctftime"),
    path("graph/", views.GraphView.as_view(), name="leaderboard-graph"),
    path("user/", views.UserListView.as_view(), name="leaderboard-user"),
    path("team/", views.TeamListView.as_view(), name="leaderboard-team"),
    path("", include(router.urls)),
]
