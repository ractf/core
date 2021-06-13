"""Token authentication for ractf."""

from rest_framework import authentication

from authentication.models import Token
from config import config


class RactfTokenAuthentication(authentication.TokenAuthentication):
    """A subclass of DRF's token authentication to add extra features."""

    model = Token

    def authenticate(self, request):
        """
        Return the user and their token if the user is authenticated.

        This will also handle maintenance mode being enabled, in which case only admins can be authenticated, bot users
        will also not be able to authenticate if bots are disabled, and the sudo attribute is set on requests if the
        current user is sudoed.
        """
        x = super(RactfTokenAuthentication, self).authenticate(request)
        if x is None:
            return None
        user, token = x
        if user.is_staff and not user.should_deny_admin:
            return user, token
        if config.get("enable_maintenance_mode"):
            return None
        if not config.get("enable_bot_users") and user.is_bot:
            return None
        if token.user_id != token.owner_id:
            request.sudo = True
            request.sudo_from = token.owner
        return user, token
