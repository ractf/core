from rest_framework.permissions import BasePermission

from member.models import TOTPStatus


class HasTwoFactor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.totp_status == TOTPStatus.ENABLED


class VerifyingTwoFactor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.totp_status == TOTPStatus.VERIFYING
