from rest_framework import throttling
from django.conf import settings


class AdminBypassThrottle(throttling.ScopedRateThrottle):
    def allow_request(self, request, view):
        if not settings.RATELIMIT_ENABLE:
            return True
        if request.user.has_admin_permissions():
            return True
        return super(AdminBypassThrottle, self).allow_request(request, view)
