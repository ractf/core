import sys

from django.apps import AppConfig




class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            # Don't run stats-related logic if we haven't migrated yet
            return

