from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from challenge.models import Challenge
from core.response import FormattedResponse


class CatchAllView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(template_name="404.html", context={"link": settings.FRONTEND_URL}, request=request, status=404)


class SelfCheckView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        issues = []

        for challenge in Challenge.objects.all():
            issues += challenge.self_check()

        return FormattedResponse(issues)
