"""Test utilities for use in this app, or shared across apps in this project."""

from typing import Any, Callable
from unittest.mock import patch

from config import config

NO_OVERRIDE = object()


def patch_config(**config_options) -> Callable:
    """A custom decorator to override config options inside a test."""

    def config_get_override(key: str) -> Any:
        """
        A 'config.get' method with our specific changes.

        The dict.get call here defaults to an arbitrary object()
        to allow overrides with values set to 'None'.
        """
        override = config_options.get(key, NO_OVERRIDE)
        if override is NO_OVERRIDE:
            return config.backend.get(key)
        return override

    def wrapper(function: Callable) -> Callable:
        """Return our test case, patched with the custom config overrides."""
        return patch("config.config.get", side_effect=config_get_override)(function)

    return wrapper
