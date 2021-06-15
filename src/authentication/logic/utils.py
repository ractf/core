"""Logic used primarily in the authentication app, or methods for auth-specific business logic."""

from datetime import datetime, timedelta

import pyotp
from django.utils import timezone


def one_day_hence() -> datetime:
    """Return the day after the current date."""
    return timezone.now() + timedelta(days=1)


def random_backup_code() -> str:
    """Return a random 8 character base32 string."""
    return pyotp.random_base32(8)
