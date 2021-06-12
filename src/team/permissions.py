"""Permissions related to teams."""

from rest_framework import permissions

from config import config


class IsTeamOwnerOrReadOnly(permissions.BasePermission):
    """Only allow read only access unless the user is the team owner."""

    def has_permission(self, request, view):
        """Return True if the user is the owner of the team or the method is safe."""
        return request.method in permissions.SAFE_METHODS or request.user.team.owner == request.user


class HasTeam(permissions.BasePermission):
    """Only allow access if the user has a team."""

    def has_permission(self, request, view):
        """Return True if the user has a team."""
        return request.user.team is not None


class TeamsEnabled(permissions.BasePermission):
    """Only allow access if teams are enabled."""

    def has_permission(self, request, view):
        """Return the value of the enable_teams config key."""
        return config.get("enable_teams")
