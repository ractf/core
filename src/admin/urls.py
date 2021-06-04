from django.urls import path
from rest_framework.routers import DefaultRouter

from admin import views

router = DefaultRouter()

urlpatterns = [
    path('self_check/', views.SelfCheckView.as_view(), name='self-check'),
]
