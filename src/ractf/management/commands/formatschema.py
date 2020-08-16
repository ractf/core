import sys

import yaml

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Format an API schema provided through stdin."

    def handle(self, *args, **options):
        """Read the API document from stdin and reformat it."""
        document = yaml.load(sys.stdin, Loader=yaml.FullLoader)
        document.update({
            "externalDocs": {
                "description": "Check us out on GitHub",
                "url": "https://github.com/ractf",
            },
            "info": {
                "title": "RACTF Core",
                "version": "",
                "description": "The API for RACTF.",
                "contact": {
                    "name": "Support",
                    "email": "support@reallyawesome.atlassian.net",
                    "url": "https://reallyawesome.atlassian.net/servicedesk/customer/portals",
                },
                "x-logo": {
                    "url": "https://www.ractf.co.uk/brand_assets/combined/wordmark_black.svg",
                    "altText": "RACTF Logo",
                },
            }
        })
        print(yaml.dump(document))
