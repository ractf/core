import os
from datetime import timezone, datetime

from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view

from backend.response import FormattedResponse
from challenge.models import Solve
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
    if users > 0:
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
def version(request):
    return FormattedResponse(
        {
            "commit_hash": os.popen("git rev-parse HEAD").read().strip()
        }
    )
