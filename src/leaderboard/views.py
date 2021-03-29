import time

from django.contrib.auth import get_user_model
from django.db.models.query import Prefetch
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Score, Solve
from config import config
from leaderboard.serializers import LeaderboardUserScoreSerializer, LeaderboardTeamScoreSerializer, \
    UserPointsSerializer, TeamPointsSerializer, CTFTimeSerializer
from team.models import Team


def should_hide_scoreboard():
    return not config.get('enable_scoreboard') and (config.get('hide_scoreboard_at') == -1 or
                                                    config.get('hide_scoreboard_at') > time.time() or
                                                    config.get('end_time') > time.time())


class CTFTimeListView(APIView):
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):
        if should_hide_scoreboard() or not config.get('enable_ctftime'):
            return Response({})
        teams = Team.objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score')
        return Response({"standings": CTFTimeSerializer(teams, many=True).data})


class GraphView(APIView):
    throttle_scope = 'leaderboard'

    def get(self, request, *args, **kwargs):
        if should_hide_scoreboard():
            return FormattedResponse({})

        graph_members = config.get('graph_members')
        top_teams = Team.objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score')[:graph_members]
        top_users = get_user_model().objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score')[
                    :graph_members]

        team_scores = Score.objects.filter(team__in=top_teams, leaderboard=True).select_related('team') \
            .order_by('-team__leaderboard_points', 'team__last_score')
        user_scores = Score.objects.filter(user__in=top_users, leaderboard=True).select_related('user') \
            .order_by('-user__leaderboard_points', 'user__last_score')

        user_serializer = LeaderboardUserScoreSerializer(user_scores, many=True)
        team_serializer = LeaderboardTeamScoreSerializer(team_scores, many=True)
        if config.get('enable_teams'):
            return FormattedResponse({'team': team_serializer.data, 'user': user_serializer.data})
        return FormattedResponse({'user': user_serializer.data})


class UserListView(ListAPIView):
    throttle_scope = 'leaderboard'
    queryset = get_user_model().objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score')
    serializer_class = UserPointsSerializer

    def list(self, request, *args, **kwargs):
        if should_hide_scoreboard():
            return FormattedResponse({})
        return super(UserListView, self).list(request, *args, **kwargs)


class TeamListView(ListAPIView):
    throttle_scope = 'leaderboard'
    queryset = Team.objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score')
    serializer_class = TeamPointsSerializer

    def list(self, request, *args, **kwargs):
        if should_hide_scoreboard():
            return FormattedResponse({})
        return super(TeamListView, self).list(request, *args, **kwargs)


class MatrixScoreboardView(APIView):
    throttle_scope = 'leaderboard'

    def get(self, request, *args, **kwargs):
        if should_hide_scoreboard():
            return FormattedResponse({})

        scoreboard = []
        teams = Team.objects.filter(is_visible=True).order_by('-leaderboard_points', 'last_score').prefetch_related(
            Prefetch('solves', queryset=Solve.objects.filter(correct=True))
        )
        for team in teams:
            scoreboard.append({
                'id': team.id,
                'name': team.name,
                'points': team.leaderboard_points,
                'solves': list(team.solves.values_list('challenge', flat=True))
            })
        return FormattedResponse(scoreboard)
