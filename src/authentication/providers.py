import abc

from plugins.providers import Provider


class RegistrationProvider(Provider, abc.ABC):
    type = 'registration'

    @abc.abstractmethod
    def register_user(self, **kwargs):
        pass


class LoginProvider(Provider, abc.ABC):
    type = 'login'

    @abc.abstractmethod
    def login_user(self, **kwargs):
        pass


class TokenProvider(Provider, abc.ABC):
    type = 'token'

    @abc.abstractmethod
    def issue_token(self, user, **kwargs):
        pass
