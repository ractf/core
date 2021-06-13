"""Define all our most basic custom authentication providers."""

from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from authentication.providers import LoginProvider, RegistrationProvider, TokenProvider
from core.exceptions import FormattedException
from core.signals import login, login_reject


class BasicAuthRegistrationProvider(RegistrationProvider):
    """A basic authentication provider for user registration."""

    name = "basic_auth"
    required_fields = ["username", "email", "password"]

    def validate(self, data: dict) -> dict:
        """Validate the provided registration form."""
        if not all(key in data for key in self.required_fields):
            raise ValidationError("A required field was not found.")

        self.validate_email(data["email"])
        self.check_email_or_username_in_use(email=data["email"], username=data["username"])

        return {key: data[key] for key in self.required_fields}

    def register_user(self, username, email, password, **_):
        """Register the provided account details once they have been validated."""
        user = get_user_model()(username=username, email=email)

        try:
            password_validation.validate_password(password, user)
        except Exception:
            raise FormattedException(status=HTTP_400_BAD_REQUEST, m="weak_password")
        user.set_password(password)

        return user


class BasicAuthLoginProvider(LoginProvider):
    """A basic authentication provider for user logins."""

    name = "basic_auth"

    def login_user(self, username, password, context, **_):
        """Given all the relevant credentials, authenticate a user's session."""
        user = authenticate(request=context.get("request"), username=username, password=password)
        if not user:
            login_reject.send(sender=self.__class__, username=username, reason="creds")
            raise FormattedException(
                m="incorrect_username_or_password",
                d={"reason": "incorrect_username_or_password"},
                status=HTTP_401_UNAUTHORIZED,
            )

        if not user.email_verified and not user.is_staff:
            login_reject.send(sender=self.__class__, username=username, reason="email")
            raise FormattedException(
                m="email_verification_required",
                d={"reason": "email_verification_required"},
                status=HTTP_401_UNAUTHORIZED,
            )

        if not user.can_login():
            login_reject.send(sender=self.__class__, username=username, reason="closed")
            raise FormattedException(m="login_not_open", d={"reason": "login_not_open"}, status=HTTP_401_UNAUTHORIZED)

        login.send(sender=self.__class__, user=user)
        return user


class BasicAuthTokenProvider(TokenProvider):
    """A basic authentication provider for token-based authentication."""

    name = "basic_auth"

    def issue_token(self, user, **_):
        """Issue a token for the provided user."""
        return user.issue_token()
