import abc
import re

from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError

from config import config
from plugins.providers import Provider


class RegistrationProvider(Provider, abc.ABC):  # pragma: no cover
    type = "registration"

    @abc.abstractmethod
    def validate(self, data):
        pass

    @abc.abstractmethod
    def register_user(self, **kwargs):
        pass

    def validate_email(self, email):
        if config.get("email_regex") and not re.compile(config.get("email_regex")).match(email):
            raise ValidationError("invalid_email")

        if config.get("email_domain") and not email.endswith(config.get("email_domain")):
            raise ValidationError("invalid_email")

        email_validator = EmailValidator()
        email_validator(email)


class LoginProvider(Provider, abc.ABC):  # pragma: no cover
    type = "login"

    @abc.abstractmethod
    def login_user(self, **kwargs):
        pass


class TokenProvider(Provider, abc.ABC):  # pragma: no cover
    type = "token"

    @abc.abstractmethod
    def issue_token(self, user, **kwargs):
        pass
