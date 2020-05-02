from django.urls import path, include
from rest_framework.routers import DefaultRouter

from member import views

router = DefaultRouter()
router.register(r'', views.MemberViewSet, basename='member')

urlpatterns = [
    path('self/', views.SelfView.as_view(), name='member-self'),
    path('', include(router.urls), name='member')
]
