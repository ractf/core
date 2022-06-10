from rest_framework import filters
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from backend.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
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
            Member
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
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return Member.objects.order_by("id").prefetch_related("team")
        return Member.objects.filter(is_visible=True).order_by("id").prefetch_related("team")


class UserIPViewSet(ModelViewSet):
    queryset = UserIP.objects.all()
    pagination_class = None
    permission_classes = (IsAdminUser,)
    serializer_class = UserIPSerializer
