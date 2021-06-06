import sys
from importlib import import_module

from django.apps import AppConfig

import team, member, challenge


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            # Don't run stats-related logic if we haven't migrated yet
            return

        from . import signals

        Team, Solve, Member = team.models.Team, challenge.models.Solve, member.models.Member

        signals.team_count.set(Team.objects.count())
        signals.solve_count.set(Solve.objects.count())
        signals.member_count.set(Member.objects.count())
        signals.correct_solve_count.set(Solve.objects.filter(correct=True).count())
