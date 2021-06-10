import sys

import psycopg2
from django.conf import settings
from django.core.management import BaseCommand
from django.core.management.commands import migrate


class Command(BaseCommand):
    help = "Resets the database to the default configuration"

    def handle(self, *args, **options):
        connection = psycopg2.connect(
            user=settings.DATABASES["default"]["USER"],
            password=settings.DATABASES["default"]["PASSWORD"],
            host=settings.DATABASES["default"]["HOST"],
            port=settings.DATABASES["default"]["PORT"],
            database="template1",
        )
        connection.set_isolation_level(0)
        cursor = connection.cursor()
        print("Dropping database...")
        cursor.execute('DROP DATABASE "%s"' % settings.DATABASES["default"]["NAME"])
        print("Creating database...")
        cursor.execute(
            'CREATE DATABASE "%s" WITH OWNER = "%s" ENCODING = "UTF8"'
            % (settings.DATABASES["default"]["NAME"], settings.DATABASES["default"]["USER"])
        )
        cursor.close()
        migrate.Command().run_from_argv(sys.argv)
