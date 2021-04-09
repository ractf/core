from collections import OrderedDict
from typing import Any

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from backend.response import FormattedResponse


class FastPagination(LimitOffsetPagination):
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
