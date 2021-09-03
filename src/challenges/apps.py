"""App for managing challenges."""

from importlib import import_module

from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    """The app config for the challenges app."""

    name = "challenges"

    def ready(self):
        """Import challenge signals when the app is ready."""
        import_module("challenges.signals", "challenges")
