from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from challenge.models import Challenge
from core.response import FormattedResponse


class SelfCheckView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        issues = []

        for challenge in Challenge.objects.all():
            issues += challenge.self_check()

        return FormattedResponse(issues)
