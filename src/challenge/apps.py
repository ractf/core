from importlib import import_module

from django.apps import AppConfig


class ChallengeConfig(AppConfig):
    name = "challenge"

    def ready(self):
        import_module("challenge.signals", "challenge")
