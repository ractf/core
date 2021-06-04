from django.apps import AppConfig


class ChallengeConfig(AppConfig):
    name = "challenge"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import challenge.signals
