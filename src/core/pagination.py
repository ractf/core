"""Pagination classes used by core."""

from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination

from core.response import FormattedResponse


class RewriteURLPagination(LimitOffsetPagination):
    """Subclass of LimitOffsetPagination to rewrite the url routes in a form that frontend understands."""

    def get_paginated_response(self, data):
        """Return a paginated response with next and previous links rewritten."""
        return FormattedResponse(
            OrderedDict(
                [
                    ("next", self.format_link(self.get_next_link())),
                    ("previous", self.format_link(self.get_previous_link())),
                    ("results", data),
                    ("count", self.count),
                ]
            )
        )

    @staticmethod
    def format_link(result):
        """Add /api/v2 into links."""
        return result if result is None else result.replace(".co.uk", ".co.uk/api/v2")
