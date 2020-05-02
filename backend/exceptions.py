from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR


class FormattedException(APIException):

    def __init__(self, d='', m='', status_code=HTTP_500_INTERNAL_SERVER_ERROR):
        super(FormattedException, self).__init__()
        self.status_code = status_code
        self.m = m
        self.d = d
