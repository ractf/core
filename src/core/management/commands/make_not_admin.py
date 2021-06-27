"""Command to forcefully remove make a user not admin."""

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    """Command to forcefully remove make a user not admin."""

    help = "Make a user not admin."

    def add_arguments(self, parser):
        """Add the user id parameter to the parser."""
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        """Make a user not admin."""
        user = get_user_model().objects.get(pk=options["user_id"])
        user.is_staff = False
        user.is_superuser = False
        user.save()
