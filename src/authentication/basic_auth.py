from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.exceptions import ValidationError

from authentication.providers import LoginProvider, TokenProvider, RegistrationProvider
from backend.exceptions import FormattedException
from backend.signals import login_reject, login


class BasicAuthRegistrationProvider(RegistrationProvider):
    name = 'basic_auth'
    required_fields = ["username", "email", "password"]

    def validate(self, data):
        print(dict(data))
        if not all(key in data for key in self.required_fields):
            raise ValidationError("A required field was not found.")

        self.validate_email(data["email"])
        self.check_email_or_username_in_use(email=data["email"], username=data["username"])

        return {key: data[key] for key in self.required_fields}

    def register_user(self, username, email, password, **kwargs):
        user = get_user_model()(
            username=username,
            email=email
        )

        password_validation.validate_password(password, user)
        user.set_password(password)

        return user


class BasicAuthLoginProvider(LoginProvider):
    name = 'basic_auth'

    def login_user(self, username, password, context, **kwargs):
        user = authenticate(request=context.get('request'),
                            username=username, password=password)
        if not user:
            login_reject.send(sender=self.__class__, username=username, reason='creds')
            raise FormattedException(m='incorrect_username_or_password', d={'reason': 'incorrect_username_or_password'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        if not user.email_verified and not user.is_superuser:
            login_reject.send(sender=self.__class__, username=username, reason='email')
            raise FormattedException(m='email_verification_required', d={'reason': 'email_verification_required'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        if not user.can_login():
            login_reject.send(sender=self.__class__, username=username, reason='closed')
            raise FormattedException(m='login_not_open', d={'reason': 'login_not_open'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        login.send(sender=self.__class__, user=user)
        return user


class BasicAuthTokenProvider(TokenProvider):
    name = 'basic_auth'

    def issue_token(self, user, **kwargs):
        return user.issue_token()
