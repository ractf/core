import time

from rest_framework import permissions

from config import config


class AdminOrReadOnlyVisible(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return request.user.is_authenticated and obj.is_visible and request.method in permissions.SAFE_METHODS


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
        return config.get('start_time') <= time.time()
