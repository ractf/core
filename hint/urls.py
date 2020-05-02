from django.urls import path, include
from rest_framework.routers import DefaultRouter

from hint import views

router = DefaultRouter()
router.register(r'', views.HintViewSet, basename='hint')

urlpatterns = [
    path('use/', views.UseHintView.as_view(), name='hint-use'),
    path('', include(router.urls)),
]
