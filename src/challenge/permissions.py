import time

from rest_framework import permissions

from config import config


class CompetitionOpen(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_staff and not request.user.should_deny_admin()) or (
            config.get("start_time") <= time.time()
            and (
                config.get("enable_view_challenges_after_competion")
                or time.time() <= config.get("end_time")
            )
        )


class HasUsedHint(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff and not request.user.should_deny_admin():
            return True
        return (
            request.method in permissions.SAFE_METHODS
            and request.user.team.hints_used.filter(hint=obj).exists()
        )

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_staff and not request.user.should_deny_admin()
        )