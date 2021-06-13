"""Custom throttling used in RACTF core."""

from django.conf import settings
from rest_framework import throttling


class AdminBypassThrottle(throttling.ScopedRateThrottle):
    """Subclass of DRF's ScopedRateThrottle to allow admins to bypass rate limits."""

    def allow_request(self, request, view):
        """Return True if the user is admin or under the ratelimit."""
        if not settings.RATELIMIT_ENABLE:
            return True
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return super(AdminBypassThrottle, self).allow_request(request, view)
