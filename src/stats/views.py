import os
from datetime import timezone, datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_prometheus.exports import ExportToDjangoView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from member.models import UserIP
from backend.response import FormattedResponse
from challenge.models import Solve, Score, Challenge
from config import config
from team.models import Team


@api_view(['GET'])
def countdown(request):
    return FormattedResponse({
        "countdown_timestamp": config.get('start_time'),
        "registration_open": config.get('register_start_time'),
        "competition_end": config.get('end_time'),
        "server_timestamp": datetime.now(timezone.utc).isoformat(),
    })


@api_view(['GET'])
def stats(request):
    users = get_user_model().objects.count()
    teams = Team.objects.count()
    if users > 0 and teams > 0:
        average = users / teams
    else:
        average = 0
    return FormattedResponse({
        "user_count": users,
        "team_count": teams,
        "solve_count": Solve.objects.count(),
        "correct_solve_count": Solve.objects.filter(correct=True).count(),
        "avg_members": average,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def full(request):
    challenge_data = {}
    for challenge in Challenge.objects.prefetch_related('solves').all():
        challenge_data[challenge.id] = {}
        challenge_data[challenge.id]["correct"] = challenge.solves.filter(correct=True).count()
        challenge_data[challenge.id]["incorrect"] = challenge.solves.filter(correct=False).count()

    point_distribution = {}
    for team in Team.objects.all():
        if not point_distribution.get(team.points):
            point_distribution[team.points] = 0
        point_distribution[team.points] += 1

    return FormattedResponse({
        "users": {
            "all": get_user_model().objects.count(),
            "confirmed": get_user_model().objects.filter(email_verified=True).count()
        },
        "teams": Team.objects.count(),
        "ips": UserIP.objects.count(),
        "total_points": Score.objects.all().aggregate(Sum('points'))["points__sum"],
        "challenges": challenge_data,
        "team_point_distribution": point_distribution
    })


@api_view(['GET'])
def version(request):
    return FormattedResponse(
        {
            "commit_hash": os.popen("git rev-parse HEAD").read().strip()
        }
    )


class PrometheusMetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        return ExportToDjangoView(request)
