from django.urls import path

from stats import views

urlpatterns = [
    path("countdown/", views.countdown, name="countdown"),
    path("stats/", views.stats, name="stats"),
    path("version/", views.version, name="version"),
    path("full/", views.full, name="full"),
    path("prometheus/", views.PrometheusMetricsView.as_view(), name="prometheus"),
]
