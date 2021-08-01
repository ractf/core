from django.http import Http404
from django.db.models import Count
from rest_framework import filters
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView

from backend.exceptions import FormattedException
from backend.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from backend.response import FormattedResponse
from backend.signals import team_join, team_join_attempt, team_join_reject
from backend.viewsets import AdminListModelViewSet
from challenge.models import Solve
from config import config
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
    serializer_class = SelfTeamSerializer
    permission_classes = (IsAuthenticated & IsTeamOwnerOrReadOnly & ReadOnlyBot,)
    throttle_scope = "self"
    pagination_class = None

    def get_object(self):
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
            .get(id=self.request.user.team.id)
        )


class TeamViewSet(AdminListModelViewSet):
    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "team"
    serializer_class = TeamSerializer
    admin_serializer_class = AdminTeamSerializer
    list_serializer_class = ListTeamSerializer
    list_admin_serializer_class = ListTeamSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "members_count"]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        if self.action == "list":
            if self.request.user.is_staff:
                qs = Team.objects.order_by("id").prefetch_related("members")
            else:
                qs = Team.objects.filter(is_visible=True).order_by("id").prefetch_related("members")
        elif self.request.user.is_staff and not self.request.user.should_deny_admin():
            qs = Team.objects.order_by("id").prefetch_related(
                "solves",
                "members",
                "hints_used",
                "solves__challenge",
                "solves__score",
                "solves__solved_by",
            )
        else:
            qs = Team.objects.filter(is_visible=True).order_by("id").prefetch_related(
                "solves",
                "members",
                "hints_used",
                "solves__challenge",
                "solves__score",
                "solves__solved_by",
            )
        return qs.annotate(members_count=Count("members"))


class CreateTeamView(CreateAPIView):
    serializer_class = CreateTeamSerializer
    model = Team
    permission_classes = (IsAuthenticated & ~HasTeam,)
    throttle_scope = "team_create"


class JoinTeamView(APIView):
    permission_classes = (IsAuthenticated & ~HasTeam & TeamsEnabled,)
    throttle_scope = "team_join"

    def post(self, request):
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
    """

    permission_classes = (IsAuthenticated & HasTeam & TeamsEnabled,)

    def post(self, request):
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
