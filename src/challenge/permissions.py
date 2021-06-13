"""Permissions for the challenge app."""

import time

from rest_framework import permissions

from config import config


class CompetitionOpen(permissions.BasePermission):
    """Permission that checks if the competition is open."""

    def has_permission(self, request, view):
        """Return if the competition is open or the action should be allowed anyway."""
        return (request.user.is_staff and not request.user.should_deny_admin) or (
            config.get("start_time") <= time.time()
            and (config.get("enable_view_challenges_after_competion") or time.time() <= config.get("end_time"))
        )
