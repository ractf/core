"""Command to forcefully remove a user from a team."""

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from teams.models import Member


class Command(BaseCommand):
    """Command to forcefully remove a user from a team."""

    help = "Removes all scores from the database"

    def add_arguments(self, parser):
        """Add the user id parameter to the parser."""
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        """Remove a user from a team."""
        user = Member.objects.get(pk=options["user_id"])
        print("Choices:", user.team.members)
        if user.team.owner == user:
            x = input("This will delete the team, are you sure?")
            if x == "n":
                return
            team = user.team
            team.delete()
            user.team = None
            user.save()
            return
        user.team = None
        user.save()
