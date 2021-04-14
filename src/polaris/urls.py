from django.urls import path, include
from rest_framework.routers import DefaultRouter

from polaris import views

router = DefaultRouter()
router.register('challenge/', views.ChallengeViewset, basename='polaris-challenge')
router.register('deployment/', views.DeploymentViewset, basename='polaris-deployment')
router.register('host/', views.HostViewset, basename='polaris-host')

urlpatterns = [
    path('get_instance/<int:challenge_id>/', views.GetInstanceView.as_view(), name='polaris-get-instance'),
    path('new_instance/<int:challenge_id>/', views.ResetInstanceView.as_view(), name='polaris-reset-instance'),
    path('', include(router.urls), name='polaris'),
    path('instances/', views.ListInstancesView.as_view(), name='polaris-list-instances'),
]
