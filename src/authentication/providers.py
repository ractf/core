import abc

from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError

import config
from plugins.providers import Provider


class RegistrationProvider(Provider, abc.ABC):  # pragma: no cover
    type = 'registration'

    @abc.abstractmethod
    def validate(self, data):
        pass

    @abc.abstractmethod
    def register_user(self, **kwargs):
        pass

    def validate_email(self, email):
        allow_domain = config.config.get('email_allow')
        if allow_domain:
            email_validator = EmailValidator(allow_domain)
        else:
            email_validator = EmailValidator()
        if email_validator(email):
            raise ValidationError('invalid_email')

    def check_email_or_username_in_use(self, email=None, username=None):
        if get_user_model().objects.filter(username=username) or get_user_model().objects.filter(email=email):
            raise ValidationError('email_or_username_in_use')


class LoginProvider(Provider, abc.ABC):  # pragma: no cover
    type = 'login'

    @abc.abstractmethod
    def login_user(self, **kwargs):
        pass


class TokenProvider(Provider, abc.ABC):  # pragma: no cover
    type = 'token'

    @abc.abstractmethod
    def issue_token(self, user, **kwargs):
        pass
