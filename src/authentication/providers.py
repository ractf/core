"""Custom base authentication providers for explicit provider definition."""

# TODO: Look for a nicer solution to this, perhaps this logic is already implemented in DRF/Django?

import abc

from django.core.validators import EmailValidator
from django.db.models import Q
from member.models import Member
from rest_framework.exceptions import ValidationError

from config import config
from core.providers import Provider


class RegistrationProvider(Provider, abc.ABC):  # pragma: no cover
    """A Provider for user registration."""

    type = "registration"

    @abc.abstractmethod
    def validate(self, data):
        """Validate the provided form data."""
        pass

    @abc.abstractmethod
    def register_user(self, **kwargs):
        """Register the user once the form data passes validation."""
        pass

    def validate_email(self, email: str) -> None:
        """Validate the email provided with Django's builtin validator."""
        allow_domain = config.get("email_allow")
        email_validator = EmailValidator(allow_domain or ...)
        if email_validator(email):
            raise ValidationError("invalid_email")

    def check_email_or_username_in_use(self, email=None, username=None):
        """Ensure that the provided email and username do not already exist."""
        if Member.objects.filter(Q(username=username) | Q(email=email)):
            raise ValidationError("email_or_username_in_use")


class LoginProvider(Provider, abc.ABC):  # pragma: no cover
    """A Provider for user logins."""

    type = "login"

    @abc.abstractmethod
    def login_user(self, **kwargs):
        """Athenticate this user with their session."""
        pass


class TokenProvider(Provider, abc.ABC):  # pragma: no cover
    """A Provider for token-based logins."""

    type = "token"

    @abc.abstractmethod
    def issue_token(self, user, **kwargs):
        """Issue a token for this user."""
        pass
