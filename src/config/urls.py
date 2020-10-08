from django.urls import path

from config import views

urlpatterns = [
    path('', views.AllConfigView.as_view()),
    path('<str:name>/', views.ConfigView.as_view())
]
