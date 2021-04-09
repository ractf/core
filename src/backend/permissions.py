import time
from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from config import config


class AdminOrReadOnlyVisible(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.user.has_admin_permissions():
            return True
        return (
            request.user.is_authenticated
            and obj.is_visible
            and request.method in permissions.SAFE_METHODS
        )


class AdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method not in permissions.SAFE_METHODS:
            return request.user.has_admin_permissions()
        return request.user.is_authenticated


class AdminOrAnonymousReadOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method not in permissions.SAFE_METHODS:
            return request.user.has_admin_permissions()
        return True


class IsCompetitionOpen(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return config.get("start_time") <= time.time()


class IsBot(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.is_bot


class ReadOnlyBot(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.user.is_authenticated and request.user.is_bot:
            return request.method not in permissions.SAFE_METHODS
        return True


class IsSudo(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return hasattr(request, 'sudo')
