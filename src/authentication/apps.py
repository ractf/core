from core.apps import PluginConfig


class AuthConfig(PluginConfig):
    name = "authentication"
    provides = [
        "authentication.basic_auth.BasicAuthLoginProvider",
        "authentication.basic_auth.BasicAuthRegistrationProvider",
        "authentication.basic_auth.BasicAuthTokenProvider",
    ]
