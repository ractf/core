"""Backends capable of storing a key-value config."""

import abc
import sys

from django.core.cache import caches
from django.db.models.query import QuerySet
from django.db.utils import OperationalError, ProgrammingError

from config.models import Config


class ConfigBackend(abc.ABC):
    """Abstract class for a config backend."""

    @abc.abstractmethod
    def get(self, key):
        """Get a config value from a given key."""
        pass

    @abc.abstractmethod
    def set(self, key, value):
        """Set a config key to a given value."""
        pass

    @abc.abstractmethod
    def get_all(self):
        """Get all config keys and values."""
        pass

    def load(self, defaults):
        """Load config keys and values from the database."""
        pass

    def save(self):
        """Save the config to a config."""
        pass


class CachedBackend(ConfigBackend):
    """A config backend using django's low level cache api."""

    @property
    def config_set(self) -> "QuerySet[Config]":
        """Get a queryset of Config objects."""
        return Config.objects

    def __init__(self):
        """Construct the backend and setup the cache."""
        self.cache = caches["default"]
        self.keys = set()

    def get(self, key):
        """Get a value for a given config key."""
        return self.cache.get(f"config_{key}")

    def set(self, key, value):
        """Set a config key and save it to the database."""
        db_config = self.config_set.filter(key="config").first()
        if db_config:
            db_config.value[key] = value
            db_config.save()
        self.cache.set(f"config_{key}", value, timeout=None)
        self.keys.add(f"config_{key}")

    def get_all(self):
        """Get all config keys and values."""
        config = {}
        for key in self.keys:
            config[key[7:]] = self.get(key[7:])
        return config

    def set_if_not_exists(self, key, value):
        """Set a config key if it doesn't exist."""
        if self.cache.add("config_" + key, value, timeout=None):
            self.keys.add(f"config_{key}")

    def load(self, defaults):
        """Load the config from the database."""
        db_config = self.config_set.filter(key="config")

        config_exists, migrations_needed = False, False
        try:
            config_exists = db_config.exists()
        except (ProgrammingError, OperationalError):  # pragma: no cover
            migrations_needed = True

        if config_exists:
            config = db_config[0].value
            if (
                "config_version" not in config
                or config["config_version"] < defaults["config_version"]
                or "test" in sys.argv
            ):
                for key, value in defaults.items():
                    self.set(key, value)
                return
            for key, value in defaults.items():
                self.set_if_not_exists(key, value)
            for key, value in config.items():
                self.set(key, value)

        elif not migrations_needed:  # pragma: no cover
            Config.objects.create(key="config", value=defaults)
            for key, value in defaults.items():
                self.set(key, value)

        self.cache.set("migrations_needed", migrations_needed)
