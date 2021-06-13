"""Exceptions defined by RACTF core."""

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR


class FormattedException(APIException):
    """Used to throw an exception that fits into *that* format, because who doesnt like throwing away useful info."""

    def __init__(self, d="", m="", status=HTTP_500_INTERNAL_SERVER_ERROR):
        """Set the message and data attributes of a formatted response."""
        super(FormattedException, self).__init__()
        self.status_code = status
        self.m = m
        self.d = d
