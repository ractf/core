from django.conf import settings
from rest_framework.views import APIView

from backend.response import FormattedResponse


class ExperimentView(APIView):
    throttle_scope = "config"

    def get(self, request):
        return FormattedResponse(settings.EXPERIMENT_OVERRIDES)
