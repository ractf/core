from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Removes a user from their team, deleting it if they are the team's owner."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        user = get_user_model().objects.get(pk=options["user_id"])
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
