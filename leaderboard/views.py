from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Score
from config import config
from leaderboard.serializers import LeaderboardUserScoreSerializer, LeaderboardTeamScoreSerializer, \
    UserPointsSerializer, TeamPointsSerializer, CTFTimeSerializer
from team.models import Team


class CTFTimeListView(APIView):
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):
        if not config.get('enable_scoreboard') or not config.get('enable_ctftime'):
            return FormattedResponse({})
        teams = Team.objects.filter(is_visible=True).order_by('-leaderboard_points')
        return FormattedResponse({"standings": CTFTimeSerializer(teams, many=True).data})


class GraphView(ListAPIView):
    throttle_scope = 'leaderboard'

    def list(self, request, *args, **kwargs):
        if not config.get('enable_scoreboard'):
            return FormattedResponse({})

        graph_members = config.get('graph_members')
        top_teams = Team.objects.filter(is_visible=True).order_by('-leaderboard_points')[:graph_members]
        top_users = get_user_model().objects.filter(is_visible=True).order_by('-leaderboard_points')[:graph_members]

        team_scores = Score.objects.filter(team__in=top_teams, leaderboard=True).select_related('team')\
            .order_by('-team__leaderboard_points')
        user_scores = Score.objects.filter(user__in=top_users, leaderboard=True).select_related('user')\
            .order_by('-user__leaderboard_points')

        user_serializer = LeaderboardUserScoreSerializer(user_scores, many=True)
        team_serializer = LeaderboardTeamScoreSerializer(team_scores, many=True)
        if config.get('enable_teams'):
            return FormattedResponse({'team': team_serializer.data, 'user': user_serializer.data})
        else:
            return FormattedResponse({'user': user_serializer.data})


class UserListView(ListAPIView):
    throttle_scope = 'leaderboard'
    queryset = get_user_model().objects.order_by('-leaderboard_points')
    serializer_class = UserPointsSerializer

    def list(self, request, *args, **kwargs):
        if not config.get('enable_scoreboard'):
            return FormattedResponse({})
        return super(UserListView, self).list(request, *args, **kwargs)


class TeamListView(ListAPIView):
    throttle_scope = 'leaderboard'
    queryset = Team.objects.order_by('-leaderboard_points')
    serializer_class = TeamPointsSerializer

    def list(self, request, *args, **kwargs):
        if not config.get('enable_scoreboard'):
            return FormattedResponse({})
        return super(TeamListView, self).list(request, *args, **kwargs)
