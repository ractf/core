from django.urls import path, include
from rest_framework.routers import DefaultRouter

from challenge import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewset, basename='categories')
router.register(r'tags', views.TagViewSet, basename='tags')
router.register(r'', views.ChallengeViewset, basename='challenges')

urlpatterns = [
    path('submit_flag/', views.FlagSubmitView.as_view(), name='submit-flag'),
    path('feedback/', views.ChallengeFeedbackView.as_view(), name='submit-feedback'),
    path('vote/', views.ChallengeVoteView.as_view(), name='vote'),
    path('files/', views.FileManagementView.as_view(), name='files'),
    path('files/delete/', views.DeleteFileView.as_view(), name='file-delete'),
    path('', include(router.urls)),
]
