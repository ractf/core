import time

from rest_framework import permissions

from config import config


class CompetitionOpen(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_staff and not request.user.should_deny_admin()) or \
               (config.get('start_time') <= time.time() and
                (config.get('enable_view_challenges_after_competion') or time.time() <= config.get('end_time')))
