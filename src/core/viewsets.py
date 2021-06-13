"""Abstractions to make common tasks with DRF viewsets easier."""

from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet


def is_exporting(request):
    """Return True if the user is exporting data."""
    return request.user.is_staff and (request.headers.get("exporting") or request.headers.get("x-exporting"))


class AdminCreateModelViewSet(ModelViewSet):
    """A subclass of ModelViewSet that uses a different serializer for admins and create requests."""

    def get_serializer_class(self):
        """Return the appropriate serializer to handle a request."""
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            if self.request.method in permissions.SAFE_METHODS:
                return self.admin_serializer_class
            return self.create_serializer_class
        return self.serializer_class


class AdminModelViewSet(ModelViewSet):
    """A viewset that subclasses ModelViewSet but uses a different serializer for admins, and normal users."""

    def get_serializer_class(self):
        """Return the appropriate serializer to handle a request."""
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            return self.admin_serializer_class
        return self.serializer_class


class AdminListModelViewSet(ModelViewSet):
    """A subclass of ModelViewSet that uses a different serializer for admins, listings and admins listings."""

    def get_serializer_class(self):
        """Return the appropriate serializer to handle a request."""
        if self.request is None:
            return self.admin_serializer_class
        if self.action == "list" and not is_exporting(self.request):
            if self.request.user.is_staff and not self.request.user.should_deny_admin:
                return self.list_admin_serializer_class
            return self.list_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            return self.admin_serializer_class
        return self.serializer_class
