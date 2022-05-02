from django.contrib.auth import get_user_model
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.viewsets import ModelViewSet

from backend.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from backend.response import FormattedResponse
from backend.viewsets import AdminListModelViewSet
from member.models import UserIP, Member
from member.serializers import (
    AdminMemberSerializer,
    ListMemberSerializer,
    MemberSerializer,
    SelfSerializer,
    UserIPSerializer,
)


class SelfView(RetrieveUpdateAPIView):
    serializer_class = SelfSerializer
    permission_classes = (IsAuthenticated & ReadOnlyBot,)
    throttle_scope = "self"

    def get_object(self):
        UserIP.hook(self.request)
        return (
            get_user_model()
            .objects.prefetch_related(
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
            .get(id=self.request.user.id)
        )


class MemberViewSet(AdminListModelViewSet):
    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "member"
    serializer_class = MemberSerializer
    admin_serializer_class = AdminMemberSerializer
    list_serializer_class = ListMemberSerializer
    list_admin_serializer_class = ListMemberSerializer
    search_fields = ["username"]
    ordering_fields = ["username", "team__name"]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        if self.action != "list":
            return get_user_model().objects.prefetch_related(
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
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return get_user_model().objects.order_by("id").prefetch_related("team")
        return get_user_model().objects.filter(is_visible=True).order_by("id").prefetch_related("team")

    @action(detail=True, methods=["post"])
    def suspend(self, request: Request, pk=None):
        member = get_object_or_404(Member, pk=pk)
        if member.is_staff:
            return FormattedResponse(status=HTTP_403_FORBIDDEN, m="cannot_suspend_staff")
        reason = request.data["reason"]
        if not isinstance(reason, str):
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)
        member.suspend(reason)
        return FormattedResponse(status=HTTP_200_OK, m="user_suspended")

    @action(detail=True, methods=["post"])
    def unsuspend(self, request: Request, pk=None):
        member = get_object_or_404(Member, pk=pk)
        member.unsuspend()
        return FormattedResponse(status=HTTP_200_OK, m="user_unsuspended")


class UserIPViewSet(ModelViewSet):
    queryset = UserIP.objects.all()
    pagination_class = None
    permission_classes = (IsAdminUser,)
    serializer_class = UserIPSerializer
