"""App managing the backend config."""

from django.apps import AppConfig

from config import config


class ConfigConfig(AppConfig):
    """The app config for the config app."""

    name = "config"

    def ready(self) -> None:
        """Load the config when django is ready."""
        config.load()
