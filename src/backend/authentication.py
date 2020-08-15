from rest_framework import authentication

from config import config


class RactfTokenAuthentication(authentication.TokenAuthentication):
    def authenticate(self, request):
        x = super(RactfTokenAuthentication, self).authenticate(request)
        if x is None:
            return None
        user, token = x
        if user.is_staff and not user.should_deny_admin():
            return user, token
        if config.get("enable_maintenance_mode"):
            return None
        if not config.get("enable_bot_users") and user.is_bot:
            return None
        return user, token
