from rest_framework import authentication

from authentication.models import Token
from config import config


class RactfTokenAuthentication(authentication.TokenAuthentication):
    model = Token

    def authenticate(self, request):
        x = super(RactfTokenAuthentication, self).authenticate(request)
        if x is None:
            return None
        user, token = x
        if token.user_id != token.owner_id:
            request.sudo = True
            request.sudo_from = token.owner
        if user.is_staff and not user.should_deny_admin():
            return user, token
        if config.get("enable_maintenance_mode"):
            return None
        if not config.get("enable_bot_users") and user.is_bot:
            return None
        if not user.is_active:
            return None

        return user, token
