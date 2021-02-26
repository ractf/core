from rest_framework import throttling
from django.conf import settings


class AdminBypassThrottle(throttling.ScopedRateThrottle):
    def allow_request(self, request, view):
        if not settings.RATELIMIT_ENABLE:
            return True
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return super(AdminBypassThrottle, self).allow_request(request, view)
