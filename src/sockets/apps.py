from django.apps import AppConfig


class SocketsConfig(AppConfig):
    name = "sockets"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import sockets.signals
