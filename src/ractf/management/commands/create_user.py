import os

from django.core.management import BaseCommand
from django.core.management.base import CommandError, CommandParser
from django.db import IntegrityError

from admin.models import AuditLogEntry
from member.models import Member


class Command(BaseCommand):
    help = "Create an arbitrary user, then generate any relevant tokens or password hashes."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username", type=str)

        parser.add_argument("--email", type=str)
        parser.add_argument("--password", type=str)

        parser.add_argument("--bot", action="store_true", help="Mark the user as a bot")
        parser.add_argument("--visible", action="store_true", help="Make the user visible")
        parser.add_argument("--staff", action="store_true", help="Make the user staff")
        parser.add_argument("--superuser", action="store_true", help="Make the user a superuser")

    def handle(self, *args, **options) -> None:
        if not options["password"]:
            options["password"] = Member.objects.make_random_password(length=14)

        if not options["email"]:
            options["email"] = options["username"] + "@bot.ractf"

        member = Member(
            username=options["username"],
            email_verified=True,
            is_visible=options["visible"],
            is_staff=options["staff"],
            is_superuser=options["superuser"],
            is_bot=options["bot"],
            email=options["email"],
        )

        try:
            member.save()
        except IntegrityError:
            raise CommandError("Username already in use")

        AuditLogEntry.create_management_entry("create_user", extra={
            "username": options["username"],
            "email_verified": True,
            "is_visible": options["visible"],
            "is_staff": options["staff"],
            "is_superuser": options["superuser"],
            "is_bot": options["bot"],
            "email": options["email"],
        })

        if member.is_bot:
            print(member.issue_token())
        else:
            member.set_password(options["password"])
