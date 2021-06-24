"""Type definitions for use throughout the app."""

from member.models import Member
from rest_framework.request import Request


class AuthenticatedRequest(Request):
    """A request that is guaranteed to have an authenticated user."""

    user: Member
