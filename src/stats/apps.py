import sys

from django.apps import AppConfig, apps
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from prometheus_client import Gauge

from backend.signals import websocket_connect, websocket_disconnect


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            # Don't run stats-related logic if we haven't migrated yet
            return

        import stats.signals
