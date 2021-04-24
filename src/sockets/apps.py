from django.apps import AppConfig


class WebsocketsConfig(AppConfig):
    name = "sockets"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import sockets.signals
