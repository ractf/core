import abc
from pydoc import locate

from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = "plugins"


class PluginConfig(AppConfig, abc.ABC):
    def ready(self):
        from plugins import providers

        if hasattr(self, "provides") and isinstance(self.provides, list):  # pragma: no cover
            for provider in map(locate, self.provides):
                providers.register_provider(provider.type, provider())
