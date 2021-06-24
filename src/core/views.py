"""Misc views for RACTF core."""

from challenge.models import Challenge
from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from core.response import FormattedResponse


class CatchAllView(TemplateView):
    """A catchall 404 view."""

    def get(self, request, *args, **kwargs):
        """Return a 404 page."""
        return render(template_name="404.html", context={"link": settings.FRONTEND_URL}, request=request, status=404)


class SelfCheckView(APIView):
    """API endpoint to run basic self checks on the challenges."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        """Return any issues found with the challenges."""
        issues = []

        for challenge in Challenge.objects.all():
            issues += challenge.self_check()

        return FormattedResponse(issues)


class ExperimentView(APIView):
    """API endpoint to override experiments on RACTF shell."""

    throttle_scope = "config"

    def get(self, request):
        """Return the list of overriden experiments."""
        return FormattedResponse(settings.EXPERIMENT_OVERRIDES)
