"""Command to transfer the owner of a team."""

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from teams.models import Team, Member


class Command(BaseCommand):
    """Command to transfer the owner of a team."""

    help = "Transfer team owner"

    def add_arguments(self, parser):
        """Add arguments to the parser."""
        parser.add_argument("user_id", type=int)
        parser.add_argument("team_id", type=int)

    def handle(self, *args, **options):
        """Switch the owner of a team."""
        user = Member.objects.get(pk=options["user_id"])
        team = Team.objects.get(pk=options["team_id"])
        team.owner = user
        team.save()
