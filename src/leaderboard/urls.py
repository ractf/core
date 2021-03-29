from django.urls import path

from leaderboard import views

urlpatterns = [
    path('ctftime/', views.CTFTimeListView.as_view(), name='leaderboard-ctftime'),
    path('graph/', views.GraphView.as_view(), name='leaderboard-graph'),
    path('user/', views.UserListView.as_view(), name='leaderboard-user'),
    path('team/', views.TeamListView.as_view(), name='leaderboard-team'),
    path('matrix/', views.MatrixScoreboardView.as_view(), name='leaderboard-matrix'),
]
