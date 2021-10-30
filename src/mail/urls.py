from django.urls import include, path
from rest_framework.routers import DefaultRouter

from mail import views

router = DefaultRouter()

urlpatterns = [
    path("list/", views.list, name="mail-list"),
]
