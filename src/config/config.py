"""Utility functions for other apps to access config."""

from pydoc import locate

from django.conf import settings
from django.utils.functional import SimpleLazyObject

backend = SimpleLazyObject(lambda: locate(settings.CONFIG["BACKEND"])())


def load():
    """Load the config."""
    backend.load(defaults=settings.DEFAULT_CONFIG)


def get(key):
    """Get a config value."""
    return backend.get(key)


def set(key, value):
    """Set a config value."""
    backend.set(key, value)


def get_all():
    """Get all config values."""
    return backend.get_all()


def get_all_non_sensitive():
    """Get all non sensitive config values."""
    sensitive = backend.get("sensitive_fields")
    config = backend.get_all()
    for field in sensitive:
        del config[field]
    return config


def is_sensitive(key):
    """Return True if a config key is sensitive."""
    return key in backend.get("sensitive_fields")
