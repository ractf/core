"""API endpoints for managing teams."""

from django.http import Http404
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView

from challenge.models import Solve
from config import config
from core.exceptions import FormattedException
from core.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from core.response import FormattedResponse
from core.signals import team_join, team_join_attempt, team_join_reject
from core.viewsets import AdminListModelViewSet
from member.models import Member
from team.models import Team
from team.permissions import HasTeam, IsTeamOwnerOrReadOnly, TeamsEnabled
from team.serializers import (
    AdminTeamSerializer,
    CreateTeamSerializer,
    ListTeamSerializer,
    SelfTeamSerializer,
    TeamSerializer,
)


class SelfView(RetrieveUpdateAPIView):
    """A view to get the details or modify the current user's team."""

    serializer_class = SelfTeamSerializer
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
    serializer_class = TeamSerializer
    admin_serializer_class = AdminTeamSerializer
    list_serializer_class = ListTeamSerializer
    list_admin_serializer_class = ListTeamSerializer
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

    @action(detail=True, methods=["POST"], permission_classes=[IsAdminUser])
    def recalculate_score(self, request, pk=None):
        """Recalculate a team's score and the scores of the users in the team."""
        team = self.get_object()
        team.recalculate_score()


class CreateTeamView(CreateAPIView):
    """View for creating a team."""

    serializer_class = CreateTeamSerializer
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
            return FormattedResponse(m="join_disabled", status=HTTP_403_FORBIDDEN)
        name = request.data.get("name")
        password = request.data.get("password")
        team_join_attempt.send(sender=self.__class__, user=request.user, name=name)
        if name and password:
            try:
                team = get_object_or_404(Team, name=name)
                if team.password != password:
                    team_join_reject.send(sender=self.__class__, user=request.user, name=name)
                    raise FormattedException(m="invalid_team_password", status=HTTP_403_FORBIDDEN)
            except Http404:
                team_join_reject.send(sender=self.__class__, user=request.user, name=name)
                raise FormattedException(m="invalid_team", status=HTTP_404_NOT_FOUND)
            team_size = int(config.get("team_size"))
            if not request.user.is_staff and not team.size_limit_exempt and 0 < team_size <= team.members.count():
                return FormattedResponse(m="team_full", status=HTTP_403_FORBIDDEN)
            request.user.team = team
            request.user.save()
            team_join.send(sender=self.__class__, user=request.user, team=team)
            return FormattedResponse()
        return FormattedResponse(m="joined_team", status=HTTP_400_BAD_REQUEST)


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
            return FormattedResponse(m="leave_disabled", status=HTTP_403_FORBIDDEN)
        if Solve.objects.filter(solved_by=request.user).exists():
            return FormattedResponse(m="challenge_solved", status=HTTP_403_FORBIDDEN)
        if request.user.team.owner == request.user:
            if Member.objects.filter(team=request.user.team).count() > 1:
                return FormattedResponse(m="cannot_leave_team_ownerless", status=HTTP_403_FORBIDDEN)
            else:
                request.user.team.delete()
        request.user.team = None
        request.user.save()
        return FormattedResponse()
