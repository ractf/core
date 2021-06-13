"""Configuration options and startup hooks for the sockets app."""

from importlib import import_module

from django.apps import AppConfig


class SocketsConfig(AppConfig):
    """App config for sockets."""

    name = "sockets"

    def ready(self):
        """Load all signals when django is ready."""
        import_module("sockets.signals", "sockets")
