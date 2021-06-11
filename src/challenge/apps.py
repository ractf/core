"""App for managing challenges."""

from importlib import import_module

from django.apps import AppConfig


class ChallengeConfig(AppConfig):
    """The app config for the challenge app."""

    name = "challenge"

    def ready(self):
        """Import challenge signals when the app is ready."""
        import_module("challenge.signals", "challenge")
