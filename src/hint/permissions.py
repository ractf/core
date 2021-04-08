from rest_framework import permissions


class HasUsedHint(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.has_admin_permissions():
            return True
        return (
            request.method in permissions.SAFE_METHODS
            and request.user.team.hints_used.filter(hint=obj).exists()
        )

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.has_admin_permissions()
