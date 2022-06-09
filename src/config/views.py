from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.views import APIView

from admin.models import AuditLogEntry
from backend.permissions import AdminOrAnonymousReadOnly
from backend.response import FormattedResponse
from config import config


class ConfigView(APIView):
    throttle_scope = "config"
    permission_classes = (AdminOrAnonymousReadOnly,)

    def get(self, request, name=None):
        if name is None:
            if request.user.is_staff:
                return FormattedResponse(config.get_all())
            return FormattedResponse(config.get_all_non_sensitive())
        if not config.is_sensitive(name) or request.user.is_staff:
            return FormattedResponse(config.get(name))
        return FormattedResponse(status=HTTP_403_FORBIDDEN)

    def post(self, request, name):
        if "value" not in request.data:
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)
        AuditLogEntry.create_entry(request.user, "set_config", {
            "old_value": config.get(name),
            "new_value": request.data.get("value"),
            "key": name,
        })
        config.set(name, request.data.get("value"))
        return FormattedResponse(status=HTTP_201_CREATED)

    def patch(self, request, name):
        if "value" not in request.data:
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)
        if config.get(name) is not None and isinstance(config.get(name), list):
            value = config.get(name)
            value.append(request.data["value"])
            AuditLogEntry.create_entry(request.user, "set_config", {
                "old_value": config.get(name),
                "new_value": value,
                "key": name,
            })
            config.set(name, value)
            return FormattedResponse()

        AuditLogEntry.create_entry(request.user, "set_config", {
            "old_value": config.get(name),
            "new_value": request.data.get("value"),
            "key": name,
        })
        config.set(name, request.data.get("value"))
        return FormattedResponse(status=HTTP_204_NO_CONTENT)
