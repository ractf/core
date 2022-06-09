from django.core.management import BaseCommand

from member.models import Member
from admin.models import AuditLogEntry


class Command(BaseCommand):
    help = "Removes a user from their team, deleting it if they are the team's owner."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        user = Member.objects.get(pk=options["user_id"])
        print("Choices:", user.team.members)
        if user.team.owner == user:
            x = input("This will delete the team, are you sure?")
            if x == "n":
                return
            AuditLogEntry.create_management_entry("unteam_delete", {"deleted_team": user.team.pk})
            team = user.team
            team.delete()
            user.team = None
            user.save()
            return
        AuditLogEntry.create_management_entry("unteam", {"user_id": user.pk})
        user.team = None
        user.save()
