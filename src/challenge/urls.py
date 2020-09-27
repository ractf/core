from django.urls import path, include
from rest_framework.routers import DefaultRouter

from challenge import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewset, basename='categories')
router.register(r'hints', views.HintViewSet, basename='hint')
router.register(r'tags', views.TagViewSet, basename='tags')
router.register(r'', views.ChallengeViewset, basename='challenges')

urlpatterns = [
    path('submit_flag/', views.FlagSubmitView.as_view(), name='submit-flag'),
    path('feedback/', views.ChallengeFeedbackView.as_view(), name='submit-feedback'),
    path('vote/', views.ChallengeVoteView.as_view(), name='vote'),
    path('files/', views.FileManagementView.as_view(), name='files'),
    path('files/delete/', views.DeleteFileView.as_view(), name='file-delete'),
    path('use_hint/', views.UseHintView.as_view(), name='hint-use'),
    path('/recalculate/team/<int:id>/', views.RecalculateTeamView.as_view(), name='recalculate-team'),
    path('/recalculate/user/<int:id>/', views.RecalculateUserView.as_view(), name='recalculate-user'),
    path('/recalculate/', views.RecalculateAllView.as_view(), name='recalculate-all'),
    path('', include(router.urls)),
]
