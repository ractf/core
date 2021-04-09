from collections import OrderedDict
from typing import Any

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from backend.response import FormattedResponse


class FastPagination(LimitOffsetPagination):
    """
    A limit/offset based style. For example:

    http://api.example.org/accounts/?limit=100
    http://api.example.org/accounts/?offset=400&limit=100

    This is subclassed from DRF's LimitOffsetPagination because of legacy url rewriting rules that we need to make the
    next and previous links comply with.
    """
    def get_paginated_response(self, data: Any) -> Response:
        return FormattedResponse(OrderedDict([
            ('next', self.format_link(self.get_next_link())),
            ('previous', self.format_link(self.get_previous_link())),
            ('results', data),
            ('count', self.count)
        ]))

    @staticmethod
    def format_link(link: str) -> str:
        return link if link is None else link.replace('.co.uk', '.co.uk/api/v2')
