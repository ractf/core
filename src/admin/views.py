from django.shortcuts import render
from django.core import mail
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Challenge


class SelfCheckView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        issues = []

        for challenge in Challenge.objects.all():
            issues += challenge.self_check()

        return FormattedResponse(issues)

def mail_list(request):
    return render(request, "mail_list.html", context={"emails": getattr(mail, 'outbox', [])})
