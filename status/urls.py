from django.urls import path

from status import views

urlpatterns = [
    path('', views.status, name='status')
]