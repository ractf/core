from rest_framework import permissions

import config


class IsTeamOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.team.owner == request.user


class HasTeam(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.team is not None


class TeamsEnabled(permissions.BasePermission):
    def has_permission(self, request, view):
        return config.config.get("enable_teams")
