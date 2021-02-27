from django.urls import path

from experiments import views

urlpatterns = [
    path('', views.ExperimentView.as_view(), name='experiments'),
]
