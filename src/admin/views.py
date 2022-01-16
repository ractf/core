from django.conf import settings
from django.core import mail
from django.http import HttpResponseNotFound
from django.shortcuts import render
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


    if settings.EMAIL_BACKEND == "anymail.backends.test.EmailBackend":
        return render(request, "mail_list.html", context={"emails": getattr(mail, 'outbox', [])})
    else:
        return HttpResponseNotFound()
