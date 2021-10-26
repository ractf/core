"""Command to forcefully remove make a user admin."""

from django.core.management import BaseCommand

from teams.models import Member


class Command(BaseCommand):
    """Command to forcefully remove make a user admin."""

    help = "Make a user admin."

    def add_arguments(self, parser):
        """Add the user id parameter to the parser."""
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        """Make a user admin."""
        user = Member.objects.get(pk=options["user_id"])
        user.is_staff = True
        user.save()
