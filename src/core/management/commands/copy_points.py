"""Command to recalculate the leaderboard_points attribute."""

import time

from challenges.models import Score
from django.core.management import BaseCommand

from config import config


class Command(BaseCommand):
    """Command to recalculate the leaderboard_points attribute."""

    help = "Removes all scores from the database"

    def handle(self, *args, **options):
        """Iterate over every score in the database and add it to the user/team's leaderboard_points."""
        if time.time() > config.get("end_time"):
            return
        for score in Score.objects.all():
            if not score.leaderboard:
                score.leaderboard = True
                score.user.leaderboard_points += score.points - score.penalty
                score.team.leaderboard_points += score.points - score.penalty
                score.solve()
                score.user.save()
                score.team.save()
