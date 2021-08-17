import sys
from importlib import import_module

from django.apps import AppConfig

import member
import team


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:  # pragma: no cover
            # Don't run stats-related logic if we haven't migrated yet
            return

        signals = import_module("stats.signals", "stats")

        Team, Member = team.models.Team, member.models.Member

        signals.team_count.set(Team.objects.count())
        signals.member_count.set(Member.objects.count())
