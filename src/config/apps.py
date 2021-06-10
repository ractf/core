from django.apps import AppConfig

from config import config


class ConfigConfig(AppConfig):
    name = "config"

    def ready(self) -> None:
        config.load()
