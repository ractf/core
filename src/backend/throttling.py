from rest_framework import throttling
from django.conf import settings
from rest_framework.request import Request


class AdminBypassThrottle(throttling.ScopedRateThrottle):
    def allow_request(self, request: Request, view: 'rest_framework.views.APIView') -> bool:
        if not settings.RATELIMIT_ENABLE:
            return True
        if request.user.has_admin_permissions():
            return True
        return super(AdminBypassThrottle, self).allow_request(request, view)
