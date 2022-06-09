from django.core.management import BaseCommand

from admin.models import AuditLogEntry
from challenge.models import Challenge, Score, Solve
from member.models import Member
from team.models import Team


class Command(BaseCommand):
    help = "Removes all scores from the database"

    def handle(self, *args, **options):
        AuditLogEntry.create_management_entry("reset_scores")
        Solve.objects.all().delete()
        Score.objects.all().delete()
        for team in Team.objects.all():
            team.points = 0
            team.leaderboard_points = 0
            team.save()
        for user in Member.objects.all():
            user.points = 0
            user.leaderboard_points = 0
            user.save()
        for challenge in Challenge.objects.all():
            challenge.first_blood = None
            challenge.save()
