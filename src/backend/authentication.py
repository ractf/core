from typing import Union, Tuple

from rest_framework import authentication
from rest_framework.request import Request

from authentication.models import Token
from config import config
from member.models import Member


class RactfTokenAuthentication(authentication.TokenAuthentication):
    """
    Simple token based authentication. Will block non-admins or admins that are being denied privileges from
    authenticating during maintenance mode and block bot users if bots are disabled. Also sets sudo properties of the
    token.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    model = Token

    def authenticate(self, request: Request) -> Union[None, Tuple[Member, bool]]:
        x = super(RactfTokenAuthentication, self).authenticate(request)
        if x is None:
            return None
        user, token = x
        if user.has_admin_permissions():
            return user, token
        if config.get("enable_maintenance_mode"):
            return None
        if not config.get("enable_bot_users") and user.is_bot:
            return None
        if token.user != token.owner:
            request.sudo = True
            request.sudo_from = token.owner
        return user, token
