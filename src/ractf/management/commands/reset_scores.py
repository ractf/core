from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from challenge.models import Score, Solve, Challenge
from team.models import Team


class Command(BaseCommand):
    help = "Removes all scores from the database"

    def handle(self, *args, **options):
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
