import traceback
from typing import Optional

from django.http import Http404

from rest_framework import exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler

import sentry_sdk

from django.conf import settings
from backend.exceptions import FormattedException
from backend.response import FormattedResponse


def handle_exception(exc: Exception, context: dict) -> Optional[Response]:
    """Handle exceptions, sending data to Sentry if errors are unhandled."""

    if "X-Reasonable" in context["request"].headers:
        return exception_handler(exc, context)

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
        response = Response(
            {"s": False, "m": "Internal server error.", "d": ""},
            status=HTTP_500_INTERNAL_SERVER_ERROR,
        )
        sentry_sdk.capture_exception(exc)
    return response
