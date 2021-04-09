import traceback

from django.http import Http404
from rest_framework import exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler

from django.conf import settings
from backend.exceptions import FormattedException
from backend.response import FormattedResponse


def handle_exception(exc: Exception, context: dict) -> Response:
    """
    Attempts to fit exceptions into the SMD format. If the X-Reasonable header is included, the exception is handled
    solely by the default handler. Instances of FormattedException will be separated out into its provided values and
    returned early. The exception is first handled by the default handler to get a base response, then if the exception
    is an instance of Http404 or PermissionDenied, a simple response will be returned with the message "not_found" or
    "permission_denied" respectively. If the exception is an instance of APIException and the detail attribute is a
    list, the code of the first element of the list will be returned in the m field, and the whole list will be included
    in the d field, if the detail attribute is a dict, the dict is iterated then the code of the first item is returned
    in m and the whole dict is returned in d, if the detail is a single item, the code is returned in m and d is
    omitted. If the exception is something else, the status code is set to 500, and the m field is set to
    "internal_server_error" and the d field is set to the string value of the exception.
    """
    if "X-Reasonable" in context['request'].headers:
        return exception_handler(exc, context)
    if settings.DEBUG:
        traceback.print_exc()
    if isinstance(exc, FormattedException):
        return FormattedResponse(s=False, d=exc.d, m=exc.m, status=exc.status_code)
    response = exception_handler(exc, context)
    if isinstance(exc, Http404):
        response.data = {"s": False, "m": "not_found", "d": ""}
    elif isinstance(exc, PermissionDenied):
        response.data = {"s": False, "m": "permission_denied", "d": ""}
    elif isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, list):
            response.data = {"s": False, "m": exc.detail[0].code, "d": exc.detail}
        elif isinstance(exc.detail, dict):
            errors = []
            for detail in exc.detail:
                for error in exc.detail[detail]:
                    errors.append(error.code)
            response.data = {"s": False, "m": errors[0], "d": exc.detail}
        else:
            response.data = {"s": False, "m": exc.detail.code, "d": ""}
    else:
        traceback.print_exc()
        response = Response(
            {"s": False, "m": "internal_server_error", "d": str(exc)}, status=HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
