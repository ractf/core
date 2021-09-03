"""App for statistics api endpoints."""
import sys
from importlib import import_module

from django.apps import AppConfig

import challenge
import member
import team


class StatsConfig(AppConfig):
    """App config for the stats app."""

    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""
        if "migrate" in sys.argv or "makemigrations" in sys.argv:  # pragma: no cover
            # Don't run stats-related logic if we haven't migrated yet
            return

        signals = import_module("stats.signals", "stats")

        Team, Solve, Member = team.models.Team, challenge.models.Solve, teams.models.Member

        signals.team_count.set(Team.objects.count())
        signals.solve_count.set(Solve.objects.count())
        signals.member_count.set(Member.objects.count())
        signals.correct_solve_count.set(Solve.objects.filter(correct=True).count())
