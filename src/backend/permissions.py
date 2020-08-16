import time

from rest_framework import permissions

from config import config


class Admin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff and not request.user.should_deny_admin()


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method not in permissions.SAFE_METHODS


class AdminOrReadOnlyVisible(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return (
            request.user.is_authenticated
            and obj.is_visible
            and request.method in permissions.SAFE_METHODS
        )


class AdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff and not request.user.should_deny_admin()
        return request.user.is_authenticated


class AdminOrAnonymousReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff and not request.user.should_deny_admin()
        return True


class IsCompetitionOpen(permissions.BasePermission):
    def has_permission(self, request, view):
        return config.get("start_time") <= time.time()


class IsBot(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_bot


class ReadOnlyBot(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_bot:
            return request.method not in permissions.SAFE_METHODS
        return True


class IsSudo(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'sudo')


class GenericPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm(self.node)


def permission(node):
    cls = type(f'GenericPermission_{node}', GenericPermission)
    cls.node = node
    return cls
