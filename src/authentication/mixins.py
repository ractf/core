"""Class mixins for authentication views and models."""

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.views import APIView

hide_password = method_decorator(
    sensitive_post_parameters(
        "password",
    )
)


class HidePasswordMixin:
    """A mixin to mark the 'password' field as a sensitive POST parameter."""

    @hide_password
    def dispatch(self, *args, **kwargs):
        """Override dispatch() with the hide_password decorator."""
        return super(APIView, self).dispatch(*args, **kwargs)
