"""A command-line tool for generating and inserting many rows of fake data into the database.

Usage:
    fake generate [--teams=<teams>] [--users=<users>] [--categories=<categories>] [--challenges=<challenges>] [--solves=<solves>] [--force]
    fake -h | --help

Options:
    --help -h                  Show this screen.
    --force                    Run even when the database is populated.

    --users=<users>            The number of users to generate per team.           [default: 2]
    --categories=<categories>  The number of categories to generate.               [default: 5]
    --teams=<teams>            The number of teams to generate.                    [default: 10]
    --challenges=<challenges>  The number of challenges to generate per category.  [default: 10]
    --solves=<solves>          The number of solves to generate.                   [default: 100]
"""

import sys
from os import environ
from pathlib import Path

import django
from docopt import docopt


arguments = docopt(__doc__)
PROJECT_BASE = str(Path(__file__).parents[2] / "src")

if PROJECT_BASE not in sys.path:
    sys.path.insert(1, PROJECT_BASE)

environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
