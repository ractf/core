from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination

from backend.response import FormattedResponse


class FastPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return FormattedResponse(OrderedDict([
            ('next', self.format_link(self.get_next_link())),
            ('previous', self.format_link(self.get_previous_link())),
            ('results', data)
        ]))

    @staticmethod
    def format_link(result):
        return result if result is None else result.replace('.co.uk', '.co.uk/api/v2')
