"""
Module used for provider registration.

A provider is a class that is capable of handling a request for a certain thing, such as logging in, registering, etc.
"""

import abc
from collections import defaultdict

from config import config

providers = defaultdict(dict)


def register_provider(provider_type, provider):
    """Register a provider."""
    providers[provider_type][provider.name] = provider


def get_provider(provider_type):
    """Get the selected provider for a provider type."""
    return providers[provider_type][config.get(provider_type + "_provider")]


class Provider(abc.ABC):
    """Base class all providers inherit from."""

    pass
