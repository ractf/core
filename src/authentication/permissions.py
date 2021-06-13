"""Set any relevant custom permissions classes for the project."""

from rest_framework.permissions import BasePermission


class HasTwoFactor(BasePermission):
    """Permission to add to any views requiring Two Factor authentication."""

    def has_permission(self, request, _):
        """Check that the user is authenticated, and that they have 2FA enabled."""
        return request.user and request.user.is_authenticated and request.user.has_2fa


class VerifyingTwoFactor(BasePermission):
    """Permission for verifying that the user's TOTP code is valid."""

    def has_permission(self, request, _):
        """Check that the user is authenticated, and has a valid verified TOTP device."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.totp_device is not None
            and not request.user.totp_device.verified
        )
