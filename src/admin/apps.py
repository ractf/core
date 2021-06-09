from django.apps import AppConfig

from config import config


class AdminConfig(AppConfig):
    name = "admin"

    def ready(self):
        config.load()
