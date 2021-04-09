from typing import Union

from django.contrib.auth.backends import ModelBackend
from rest_framework.request import Request

from member.models import Member

UserModel = Member


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticates against members.models.Member.
    """

    def authenticate(self, request: Request, username: str = None, password: str = None, **kwargs) -> Union[Member, None]:
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
