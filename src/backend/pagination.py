from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination

from backend.response import FormattedResponse


class FastPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return FormattedResponse(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
