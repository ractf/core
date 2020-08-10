from rest_framework.permissions import BasePermission


class HasTwoFactor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.has_2fa()


class VerifyingTwoFactor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.totp_device is not None \
               and not request.user.totp_device.verified
