from django.urls import path

from challengeserver import views

urlpatterns = [
    path('instance/<str:challenge_id>/', views.RequestInstanceOrGetCurrentInstance.as_view(), name='get-existing-or-create-new'),
    path('reset/<str:challenge_id>/', views.RequestReset.as_view(), name='request-new-instance'),
    path('disconnect/', views.DisconnectFromAllInstances.as_view(), name='disconnect-from-all-instances'),
]
