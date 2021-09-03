"""Pagination classes used by core."""

from collections import OrderedDict
from typing import Optional
from urllib import parse

from rest_framework.pagination import LimitOffsetPagination

from core.response import FormattedResponse


def prepend_api_prefix(url: Optional[str] = None) -> Optional[str]:
    """Given a full URL as a string, prepend the /api/v2 prefix."""
    if url is None:
        return
    result = parse.urlparse(url)
    return f"{result.scheme}://{result.netloc}/api/v2{result.path}?{result.query}"


class FormattedPagination(LimitOffsetPagination):
    def get_next_link(self) -> Optional[str]:
        return prepend_api_prefix(super().get_next_link())

    def get_previous_link(self) -> Optional[str]:
        return prepend_api_prefix(super().get_previous_link())

    def get_paginated_response(self, data):
        """Return a paginated response with next and previous links rewritten."""
        return FormattedResponse(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("count", self.count),
                ]
            )
        )
