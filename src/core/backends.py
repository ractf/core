"""Authentication backends define by RACTF core."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Authenticates against settings.AUTH_USER_MODEL."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Return a user object if authentication is successful or None.

        This is a copy of django's default authentication backend, except it uses the @ character to switch to email.
        """
        try:
            if "@" in username:
                user = UserModel.objects.get(email=username)
            else:
                user = UserModel.objects.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
