from django.urls import path

from stats import views

urlpatterns = [
    path('countdown/', views.countdown, name='countdown'),
    path('stats/', views.stats, name='stats'),
    path('version/', views.version, name='version')
]
