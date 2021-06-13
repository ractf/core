"""Configuration options and startup hooks for the authentication app."""

from core.apps import PluginConfig


class AuthConfig(PluginConfig):
    """Define providers and relevant metadata for the authentication app."""

    name = "authentication"
    provides = [
        "authentication.basic_auth.BasicAuthLoginProvider",
        "authentication.basic_auth.BasicAuthRegistrationProvider",
        "authentication.basic_auth.BasicAuthTokenProvider",
    ]
