"""Type definitions for use throughout the app."""

from rest_framework.request import Request

from teams.models import Member


class AuthenticatedRequest(Request):
    """A request that is guaranteed to have an authenticated user."""

    user: Member
