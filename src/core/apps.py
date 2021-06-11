import abc
from pydoc import locate

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import ERROR, WARNING, CheckMessage, Tags, register

from core import plugins


class CoreConfig(AppConfig):
    name = "core"

    def ready(self) -> None:
        plugins.load_plugins(settings.INSTALLED_PLUGINS)


class PluginConfig(AppConfig, abc.ABC):
    def ready(self):
        from core import providers

        if hasattr(self, "provides") and isinstance(self.provides, list):  # pragma: no cover
            for provider in map(locate, self.provides):
                providers.register_provider(provider.type, provider())


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
