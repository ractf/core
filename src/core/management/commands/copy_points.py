import time

from django.core.management import BaseCommand

from challenge.models import Score
from config import config


class Command(BaseCommand):
    help = "Removes all scores from the database"

    def handle(self, *args, **options):
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
