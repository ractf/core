import abc
import re

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from config import config
from plugins.providers import Provider


class RegistrationProvider(Provider, abc.ABC):
    type = 'registration'

    @abc.abstractmethod
    def validate(self, data):
        pass

    @abc.abstractmethod
    def register_user(self, **kwargs):
        pass

    def validate_email(self, email):
        if config.get('email_regex') and not re.compile(config.get('email_regex')).match(email) or \
                not email.endswith(config.get('email_domain')):
            raise ValidationError('invalid_email')

    def check_email_or_username_in_use(self, email=None, username=None):
        if get_user_model().objects.filter(username=username) or get_user_model().objects.filter(email=email):
            raise ValidationError('email_or_username_in_use')


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
