"""Permissions for the hint app."""

from rest_framework import permissions


class HasUsedHint(permissions.BasePermission):
    """Permission based on if a user/team has used a hint."""

    def has_object_permission(self, request, view, obj):
        """Return True if the user/team has used this hint."""
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return request.method in permissions.SAFE_METHODS and request.user.team.hints_used.filter(hint=obj).exists()

    def has_permission(self, request, view):
        """Return True if the user can use a specific http method to access hints."""
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_staff and not request.user.should_deny_admin()
        )
