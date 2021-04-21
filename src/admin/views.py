from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Challenge


class SelfCheckView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        issues = []

        for challenge in Challenge.objects.all():
            challenge.self_check()

        return FormattedResponse(issues)
