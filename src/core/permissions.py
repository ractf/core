"""Permission classes used throughout RACTF Core."""

from rest_framework import permissions


class AdminOrReadOnlyVisible(permissions.BasePermission):
    """Allow the user access to an object if they are admin, or using a safe method on a visible object."""

    def has_object_permission(self, request, view, obj):
        """Return True if the user can access this object."""
        if request.user.is_staff and not request.user.should_deny_admin:
            return True
        return request.user.is_authenticated and obj.is_visible and request.method in permissions.SAFE_METHODS


class AdminOrReadOnly(permissions.BasePermission):
    """Allow the user access to a view if they are admin, or using a safe method."""

    def has_permission(self, request, view):
        """Return True if the user can access this view."""
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff and not request.user.should_deny_admin
        return request.user.is_authenticated


class AdminOrAnonymousReadOnly(permissions.BasePermission):
    """Allow a possible unauthenticated user access to a view if they are admin, or using a safe method."""

    def has_permission(self, request, view):
        """Return True if the user can access this view."""
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff and not request.user.should_deny_admin
        return True


class IsBot(permissions.BasePermission):
    """Allow the user access to a view if they are a bot."""

    def has_permission(self, request, view):
        """Return True if the user can access this view."""
        return request.user.is_authenticated and request.user.is_bot


class ReadOnlyBot(permissions.BasePermission):
    """Allow the user read only access to a view if they are a bot."""

    def has_permission(self, request, view):
        """Return True if the user can access this view."""
        if request.user.is_authenticated and request.user.is_bot:
            return request.method in permissions.SAFE_METHODS
        return True


class IsSudo(permissions.BasePermission):
    """Allow the user access to a view if impersonating another user."""

    def has_permission(self, request, view):
        """Return True if the user can access this view."""
        return hasattr(request, "sudo")
