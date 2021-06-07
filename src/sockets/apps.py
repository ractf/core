from importlib import import_module

from django.apps import AppConfig


class SocketsConfig(AppConfig):
    name = "sockets"

    def ready(self):
        import_module("sockets.signals", "sockets")
