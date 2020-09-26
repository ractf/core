from django.http import Http404
from rest_framework import filters
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    CreateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from backend.exceptions import FormattedException
from backend.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from backend.response import FormattedResponse
from backend.signals import team_join_attempt, team_join_reject, team_join
from backend.viewsets import AdminListModelViewSet
from config import config
from team.models import Team
from challenge.models import Solve
from team.permissions import IsTeamOwnerOrReadOnly, HasTeam, TeamsEnabled
from team.serializers import (
    SelfTeamSerializer,
    TeamSerializer,
    CreateTeamSerializer,
    AdminTeamSerializer,
    ListTeamSerializer,
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
            ).get(id=self.request.user.team.id)
        )


class TeamViewSet(AdminListModelViewSet):
    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "team"
    serializer_class = TeamSerializer
    admin_serializer_class = AdminTeamSerializer
    list_serializer_class = ListTeamSerializer
    list_admin_serializer_class = ListTeamSerializer
    search_fields = ["name"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        if self.action == "list":
            if self.request.user.is_superuser:
                return Team.objects.order_by("id").prefetch_related("members")
            return Team.objects.filter(is_visible=True).order_by("id").prefetch_related("members")
        if self.request.user.is_superuser and not self.request.user.should_deny_admin():
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
            if not Team.objects.filter(name__iexact=name).exists():
                team_join_reject.send(sender=self.__class__, user=request.user, name=name)
                raise FormattedException(status_code=HTTP_404_NOT_FOUND)
            team = Team.objects.get(name__iexact=name)
            if team.password != password:
                raise FormattedException(status_code=HTTP_401_UNAUTHORIZED)
            team_size = int(config.get('team_size'))
            if not request.user.is_staff and not team.size_limit_exempt and 0 < team_size <= team.members.count():
                return FormattedResponse(m='team_full', status=HTTP_403_FORBIDDEN)
            request.user.team = team
            request.user.save()
            team_join.send(sender=self.__class__, user=request.user, team=team)
            return FormattedResponse()
        return FormattedResponse(m='joined_team', status=HTTP_400_BAD_REQUEST)


class LeaveTeamView(APIView):
    permission_classes = (IsAuthenticated & HasTeam & TeamsEnabled,)

    def post(self, request):
        if not config.get('enable_team_leave'):
            return FormattedResponse(m='leave_disabled', status=HTTP_403_FORBIDDEN)
        if Solve.objects.filter(solved_by=request.user).exists():
            return FormattedResponse(m='challenge_solved', status=HTTP_403_FORBIDDEN)
        request.user.team = None
        request.user.save()
        return FormattedResponse()
