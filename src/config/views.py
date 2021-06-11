"""API endpoints to manage the backend config."""

from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.views import APIView

from config import config
from core.permissions import AdminOrAnonymousReadOnly
from core.response import FormattedResponse


class ConfigView(APIView):
    """APIView to handle config."""

    throttle_scope = "config"
    permission_classes = (AdminOrAnonymousReadOnly,)

    def get(self, request, name=None):
        """Return the whole config, or a specific key if the user has permissions to see it."""
        if name is None:
            if request.user.is_staff:
                return FormattedResponse(config.get_all())
            return FormattedResponse(config.get_all_non_sensitive())
        if not config.is_sensitive(name) or request.user.is_staff:
            return FormattedResponse(config.get(name))
        return FormattedResponse(status=HTTP_403_FORBIDDEN)

    def post(self, request, name):
        """Create or update a config key."""
        if "value" not in request.data:
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)
        config.set(name, request.data.get("value"))
        return FormattedResponse(status=HTTP_201_CREATED)

    def patch(self, request, name):
        """Create or update a config key."""
        if "value" not in request.data:
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)
        if config.get(name) is not None and isinstance(config.get(name), list):
            value = config.get(name)
            value.append(request.data["value"])
            config.set(name, value)
            return FormattedResponse()
        config.set(name, request.data.get("value"))
        return FormattedResponse(status=HTTP_204_NO_CONTENT)
