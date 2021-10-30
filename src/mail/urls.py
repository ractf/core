from django.urls import path
from rest_framework.routers import DefaultRouter

from mail import views

urlpatterns = [
    path("list/", views.list, name="mail-list"),
]
