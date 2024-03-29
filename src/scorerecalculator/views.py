from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Score
from member.models import Member
from team.models import Team


def recalculate_team(team):
    team.points = 0
    team.leaderboard_points = 0
    for user in team.members.all():
        with transaction.atomic():
            recalculate_user(user)
            team.points += user.points
            team.leaderboard_points += user.leaderboard_points
    team.save()


def recalculate_user(user):
    user.points = 0
    user.leaderboard_points = 0
    scores = Score.objects.filter(user=user)
    for score in scores:
        if score.leaderboard:
            user.leaderboard_points += score.points - score.penalty
        user.points += score.points - score.penalty
    user.save()


class RecalculateTeamView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, id):
        with transaction.atomic():
            team = get_object_or_404(Team.objects.select_for_update(), id=id)
            recalculate_team(team)
        return FormattedResponse()


class RecalculateUserView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, id):
        with transaction.atomic():
            user = get_object_or_404(Member.objects.select_for_update(), id=id)
            recalculate_user(user)
        return FormattedResponse()


class RecalculateAllView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        with transaction.atomic():
            for team in Team.objects.select_for_update().all():
                recalculate_team(team)
        return FormattedResponse()
