from django.apps import AppConfig


class WebsocketsConfig(AppConfig):
    name = "websockets"

    def ready(self):
        # noinspection PyUnresolvedReferences
        pass
