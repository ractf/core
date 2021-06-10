from django.apps import AppConfig
from django.conf import settings
from django.core.checks import ERROR, WARNING, CheckMessage, Tags, register


class CoreConfig(AppConfig):
    name = "core"


@register(Tags.compatibility)
def check_settings(app_configs, **kwargs):  # pragma: no cover
    errors = []
    for setting in settings.REQUIRED_SETTINGS:
        if getattr(settings, setting, None) is None:
            errors.append(
                CheckMessage(
                    (WARNING if settings.DEBUG else ERROR),
                    f"Required setting {setting} was missing.",
                    hint="Did you forget to set an environment variable?",
                    id="ractf.E001",
                )
            )
    return errors
