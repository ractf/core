import sys

from django.apps import AppConfig

import challenge
import member
import stats
import team


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            # Don't run stats-related logic if we haven't migrated yet
            return

        Team, Solve, Member = team.models.Team, challenge.models.Solve, member.models.Member

        stats.signals.team_count.set(Team.objects.count())
        stats.signals.solve_count.set(Solve.objects.count())
        stats.signals.member_count.set(Member.objects.count())
        stats.signals.correct_solve_count.set(Solve.objects.filter(correct=True).count())
