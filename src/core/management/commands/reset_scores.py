"""Command to remove all scores from the database."""

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from challenge.models import Challenge, Score, Solve
from team.models import Team


class Command(BaseCommand):
    """Command to remove all scores from the database."""

    help = "Removes all scores from the database"

    def handle(self, *args, **options):
        """
        Reset all teams and users to 0 points, remove all scores and solves,
        and remove first bloods from all challenges.
        """
        Solve.objects.all().delete()
        Score.objects.all().delete()
        for team in Team.objects.all():
            team.points = 0
            team.leaderboard_points = 0
            team.save()
        for user in get_user_model().objects.all():
            user.points = 0
            user.leaderboard_points = 0
            user.save()
        for challenge in Challenge.objects.all():
            challenge.first_blood = None
            challenge.save()
