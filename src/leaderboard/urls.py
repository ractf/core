from django.urls import path, include
from rest_framework.routers import DefaultRouter

from leaderboard import views

router = DefaultRouter()
router.register('matrix/', views.MatrixScoreboardView, basename='leaderboard-matrix')
router.register('matrix/<str:scoreboard>', views.MatrixScoreboardView, basename='leaderboard-matrix')

urlpatterns = [
    path('ctftime/', views.CTFTimeListView.as_view(), name='leaderboard-ctftime'),
    path('graph/', views.GraphView.as_view(), name='leaderboard-graph'),
    path('graph/<str:scoreboard>/', views.GraphView.as_view(), name='leaderboard-graph-subscoreboard'),
    path('user/', views.UserListView.as_view(), name='leaderboard-user'),
    path('team/', views.TeamListView.as_view(), name='leaderboard-team'),
    path('team/<str:scoreboard>/', views.TeamListView.as_view(), name='leaderboard-team-subscoreboard'),
    path('', include(router.urls)),
]
