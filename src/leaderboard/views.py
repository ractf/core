"""API routes for the leaderboard app."""

import time

from django.contrib.auth import get_user_model
from django.core.cache import caches
from rest_framework.generics import ListAPIView
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from challenge.models import Score
from config import config
from core.response import FormattedResponse
from leaderboard.serializers import (
    CTFTimeSerializer,
    LeaderboardTeamScoreSerializer,
    LeaderboardUserScoreSerializer,
    MatrixSerializer,
    TeamPointsSerializer,
    UserPointsSerializer,
)
from team.models import Team


def should_hide_scoreboard():
    """Return True if the scoreboard should be hidden."""
    return not config.get("enable_scoreboard") and (
        config.get("hide_scoreboard_at") == -1
        or config.get("hide_scoreboard_at") > time.time()
        or config.get("end_time") > time.time()
    )


class CTFTimeListView(APIView):
    """CTFTime scoreboard integration."""

    renderer_classes = (
        JSONRenderer,
        BrowsableAPIRenderer,
    )

    def get(self, request, *args, **kwargs):
        """Get the scoreboard in a CTFTime compatible format."""
        if should_hide_scoreboard() or not config.get("enable_ctftime"):
            return Response({})
        teams = Team.objects.visible().ranked()
        return Response({"standings": CTFTimeSerializer(teams, many=True).data})


class GraphView(APIView):
    """API endpoint to display the leaderboard as a graph."""

    throttle_scope = "leaderboard"

    def get(self, request, *args, **kwargs):
        """Return the points to plot on the graph."""
        if should_hide_scoreboard():
            return FormattedResponse({})

        cache = caches["default"]
        cached_leaderboard = cache.get("leaderboard_graph")
        if cached_leaderboard is not None and config.get("enable_caching"):
            return FormattedResponse(cached_leaderboard)

        graph_members = config.get("graph_members")
        top_teams = Team.objects.visible().ranked()[:graph_members]
        top_users = (
            get_user_model()
            .objects.filter(is_visible=True)
            .order_by("-leaderboard_points", "last_score")[:graph_members]
        )

        team_scores = (
            Score.objects.filter(team__in=top_teams, leaderboard=True)
            .select_related("team")
            .order_by("-team__leaderboard_points", "team__last_score")
        )
        user_scores = (
            Score.objects.filter(user__in=top_users, leaderboard=True)
            .select_related("user")
            .order_by("-user__leaderboard_points", "user__last_score")
        )

        user_serializer = LeaderboardUserScoreSerializer(user_scores, many=True)
        team_serializer = LeaderboardTeamScoreSerializer(team_scores, many=True)
        response = {"user": user_serializer.data}
        if config.get("enable_teams"):
            response["team"] = team_serializer.data

        cache.set("leaderboard_graph", response, 15)
        return FormattedResponse(response)


class UserListView(ListAPIView):
    """API endpoint to display the user scoreboard."""

    throttle_scope = "leaderboard"
    queryset = get_user_model().objects.filter(is_visible=True).order_by("-leaderboard_points", "last_score")
    serializer_class = UserPointsSerializer

    def list(self, request, *args, **kwargs):
        """Return a list of users and how many points they have."""
        if should_hide_scoreboard():
            return FormattedResponse({})
        return super(UserListView, self).list(request, *args, **kwargs)


class TeamListView(ListAPIView):
    """API endpoint to display the team scoreboard."""

    throttle_scope = "leaderboard"
    queryset = Team.objects.visible().ranked()
    serializer_class = TeamPointsSerializer

    def list(self, request, *args, **kwargs):
        """Return a list of teams and how many points they have."""
        if should_hide_scoreboard():
            return FormattedResponse({})
        return super(TeamListView, self).list(request, *args, **kwargs)


class MatrixScoreboardView(ReadOnlyModelViewSet):
    """API endpoint to display the matrix scoreboard."""

    throttle_scope = "leaderboard"
    queryset = Team.objects.visible().ranked().prefetch_solves()
    serializer_class = MatrixSerializer

    def list(self, request, *args, **kwargs):
        """Return a list of teams and which challenges they have solved."""
        if should_hide_scoreboard():
            return FormattedResponse({})
        return super(MatrixScoreboardView, self).list(request, *args, **kwargs)
