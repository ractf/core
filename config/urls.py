from django.urls import path

from config import views

urlpatterns = [
    path('', views.ConfigView.as_view()),
    path('<str:name>/', views.ConfigView.as_view())
]
