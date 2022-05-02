from json import dumps

from django.core.management import BaseCommand

from member.models import UserIP


class Command(BaseCommand):
    help = "Group users by source IP address to try and spot cheating."

    def add_arguments(self, parser):
        parser.add_argument(
            '--multiple',
            action='store_true',
            help='Show only IP addresses with multiple users',
        )

        parser.add_argument(
            '--json',
            action='store_true',
            help='Output JSON',
        )

    def handle(self, *args, **options) -> None:
        self.stderr.write(self.style.WARNING("Due to use of CGNAT, source IP addresses may be unreliable. Proceed with caution."))

        ips = UserIP.objects.all()

        grouped = {}

        for ip in ips:
            if ip.ip not in grouped:
                grouped[ip.ip] = []
            if ip.user.username not in grouped[ip.ip]:
                grouped[ip.ip].append(ip.user.username)

        if options["multiple"]:
            multiple_grouped = {}

            for group in grouped.items():
                if len(group[1]) > 1:
                    multiple_grouped |= {group[0]: group[1]}

            grouped = multiple_grouped

        if options["json"]:
            self.stdout.write(dumps(grouped))
        else:
            self.stdout.write(str(grouped))
