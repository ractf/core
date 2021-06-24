"""API endpoints for managing teams."""

from django.http import Http404
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from challenge.models import Solve
from config import config
from core.exceptions import FormattedException
from core.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from core.response import FormattedResponse
from core.signals import team_join, team_join_attempt, team_join_reject
from core.viewsets import AdminListModelViewSet
from teams import serializers
from teams.models import Member, Team, UserIP
from teams.permissions import HasTeam, IsTeamOwnerOrReadOnly, TeamsEnabled


class SelfTeamView(RetrieveUpdateAPIView):
    """A view to get the details or modify the current user's team."""

    serializer_class = serializers.SelfTeamSerializer
    permission_classes = (IsAuthenticated & IsTeamOwnerOrReadOnly & ReadOnlyBot,)
    throttle_scope = "self"
    pagination_class = None

    def get_object(self):
        """Get the current user's team or 404."""
        if self.request.user.team is None:
            raise Http404()
        return (
            Team.objects.order_by("id")
            .prefetch_related(
                "solves",
                "members",
                "hints_used",
                "solves__challenge",
                "solves__score",
                "solves__solved_by",
            )
            .get(id=self.request.user.team.pk)
        )


class TeamViewSet(AdminListModelViewSet):
    """View and modify other teams."""

    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "team"
    serializer_class = serializers.TeamSerializer
    admin_serializer_class = serializers.AdminTeamSerializer
    list_serializer_class = serializers.ListTeamSerializer
    list_admin_serializer_class = serializers.ListTeamSerializer
    search_fields = ["name"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        """Get the queryset containing the relevant team(s) and details."""
        if self.action == "list":
            if self.request.user.is_staff:
                return Team.objects.order_by("id").prefetch_related("members")
            return Team.objects.filter(is_visible=True).order_by("id").prefetch_related("members")
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            return Team.objects.order_by("id").prefetch_related(
                "solves",
                "members",
                "hints_used",
                "solves__challenge",
                "solves__score",
                "solves__solved_by",
            )
        return (
            Team.objects.filter(is_visible=True)
            .order_by("id")
            .prefetch_related(
                "solves",
                "members",
                "hints_used",
                "solves__challenge",
                "solves__score",
                "solves__solved_by",
            )
        )

    @action(methods=["POST"], detail=True, permission_classes=[IsAdminUser])
    def recalculate_score(self, request, pk=None):
        """Recalculate the score of a team and its members."""
        team = self.get_object()
        team.recalculate_score()
        return FormattedResponse(d={"points": team.points, "leaderboard_points": team.leaderboard_points})

    @action(methods=["POST"], detail=False, permission_classes=[IsAdminUser])
    def recalculate_all_scores(self, request):
        """Recalculate the scores of every team and their members."""
        teams = self.get_queryset()
        for team in teams:
            team.recalculate_score()
        return FormattedResponse()


class CreateTeamView(CreateAPIView):
    """View for creating a team."""

    serializer_class = serializers.CreateTeamSerializer
    model = Team
    permission_classes = (IsAuthenticated & ~HasTeam,)
    throttle_scope = "team_create"


class JoinTeamView(APIView):
    """Endpoint for the user joining a team."""

    permission_classes = (IsAuthenticated & ~HasTeam & TeamsEnabled,)
    throttle_scope = "team_join"

    def post(self, request):
        """Check if the user can join a team, and add them to it."""
        if not config.get("enable_team_join"):
            return FormattedResponse(m="join_disabled", status=status.HTTP_403_FORBIDDEN)
        name = request.data.get("name")
        password = request.data.get("password")
        team_join_attempt.send(sender=self.__class__, user=request.user, name=name)
        if name and password:
            try:
                team = get_object_or_404(Team, name=name)
                if team.password != password:
                    team_join_reject.send(sender=self.__class__, user=request.user, name=name)
                    raise FormattedException(m="invalid_team_password", status=status.HTTP_403_FORBIDDEN)
            except Http404:
                team_join_reject.send(sender=self.__class__, user=request.user, name=name)
                raise FormattedException(m="invalid_team", status=status.HTTP_404_NOT_FOUND)
            team_size = int(config.get("team_size"))
            if not request.user.is_staff and not team.size_limit_exempt and 0 < team_size <= team.members.count():
                return FormattedResponse(m="team_full", status=status.HTTP_403_FORBIDDEN)
            request.user.team = team
            request.user.save()
            team_join.send(sender=self.__class__, user=request.user, team=team)
            return FormattedResponse()
        return FormattedResponse(m="joined_team", status=status.HTTP_400_BAD_REQUEST)


class LeaveTeamView(APIView):
    """
    Remove the authenticated user from a team.

    If the user is the owner of the team, they will be blocked from leaving if the team is not empty,
    else the team is deleted.
    """

    permission_classes = (IsAuthenticated & HasTeam & TeamsEnabled,)

    def post(self, request):
        """Leave the team and return if it was successful."""
        if not config.get("enable_team_leave"):
            return FormattedResponse(m="leave_disabled", status=status.HTTP_403_FORBIDDEN)
        if Solve.objects.filter(solved_by=request.user).exists():
            return FormattedResponse(m="challenge_solved", status=status.HTTP_403_FORBIDDEN)
        if request.user.team.owner == request.user:
            if Member.objects.filter(team=request.user.team).count() > 1:
                return FormattedResponse(m="cannot_leave_team_ownerless", status=status.HTTP_403_FORBIDDEN)
            else:
                request.user.team.delete()
        request.user.team = None
        request.user.save()
        return FormattedResponse()


class SelfView(RetrieveUpdateAPIView):
    """API endpoints for viewing and updating the current user."""

    serializer_class = serializers.SelfSerializer
    permission_classes = (IsAuthenticated & ReadOnlyBot,)
    throttle_scope = "self"

    def get_object(self):
        """Get the current member with some prefetches."""
        UserIP.hook(self.request)
        return (
            Member.objects.prefetch_related(
                "team",
                "team__solves",
                "team__solves__score",
                "team__hints_used",
                "team__solves__challenge",
                "team__solves__solved_by",
                "solves",
                "solves__score",
                "hints_used",
                "solves__challenge",
                "solves__team",
                "solves__score__team",
            )
            .distinct()
            .get(id=self.request.user.pk)
        )


class MemberViewSet(AdminListModelViewSet):
    """Viewset for viewing and updating members."""

    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "member"
    serializer_class = serializers.MemberSerializer
    admin_serializer_class = serializers.AdminMemberSerializer
    list_serializer_class = serializers.ListMemberSerializer
    list_admin_serializer_class = serializers.ListMemberSerializer
    search_fields = ["username", "email"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        """Return the queryset for the member or list of members."""
        if self.action != "list":
            return Member.objects.prefetch_related(
                "team",
                "team__solves",
                "team__solves__score",
                "team__hints_used",
                "team__solves__challenge",
                "team__solves__solved_by",
                "solves",
                "solves__score",
                "hints_used",
                "solves__challenge",
                "solves__team",
                "solves__score__team",
            )
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            return Member.objects.order_by("id").prefetch_related("team")
        return Member.objects.filter(is_visible=True).order_by("id").prefetch_related("team")


class UserIPViewSet(ModelViewSet):
    """Viewset for managing UserIP objects."""

    queryset = UserIP.objects.all()
    pagination_class = None
    permission_classes = (IsAdminUser,)
    serializer_class = serializers.UserIPSerializer
