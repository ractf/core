"""App config for the core app, abstract app config for apps that provide plugins and a self check."""

import abc
from pydoc import locate

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import ERROR, WARNING, CheckMessage, Tags, register

from core import plugins


class CoreConfig(AppConfig):
    """App config for the core app."""

    name = "core"

    def ready(self) -> None:
        """Load plugins when django is ready."""
        plugins.load_plugins(settings.INSTALLED_PLUGINS)


class PluginConfig(AppConfig, abc.ABC):
    """Base class for app configs that provide plugins."""

    def ready(self):
        """Register plugin providers when django is ready."""
        from core import providers

        if hasattr(self, "provides") and isinstance(self.provides, list):  # pragma: no cover
            for provider in map(locate, self.provides):
                providers.register_provider(provider.type, provider())


@register(Tags.compatibility)
def check_settings(app_configs, **kwargs):  # pragma: no cover
    """Check that no required settings are missing."""
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
