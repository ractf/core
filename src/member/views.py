"""API routes for the Member app."""

from django.contrib.auth import get_user_model
from rest_framework import filters
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from core.viewsets import AdminListModelViewSet
from member.models import UserIP
from member.serializers import (
    AdminMemberSerializer,
    ListMemberSerializer,
    MemberSerializer,
    SelfSerializer,
    UserIPSerializer,
)


class SelfView(RetrieveUpdateAPIView):
    """API endpoints for viewing and updating the current user."""

    serializer_class = SelfSerializer
    permission_classes = (IsAuthenticated & ReadOnlyBot,)
    throttle_scope = "self"

    def get_object(self):
        """Get the current member with some prefetches."""
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
            .get(id=self.request.user.pk)
        )


class MemberViewSet(AdminListModelViewSet):
    """Viewset for viewing and updating members."""

    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = "member"
    serializer_class = MemberSerializer
    admin_serializer_class = AdminMemberSerializer
    list_serializer_class = ListMemberSerializer
    list_admin_serializer_class = ListMemberSerializer
    search_fields = ["username", "email"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        """Return the queryset for the member or list of members."""
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
        if self.request.user.is_staff and not self.request.user.should_deny_admin:
            return get_user_model().objects.order_by("id").prefetch_related("team")
        return get_user_model().objects.filter(is_visible=True).order_by("id").prefetch_related("team")


class UserIPViewSet(ModelViewSet):
    """Viewset for managing UserIP objects."""

    queryset = UserIP.objects.all()
    pagination_class = None
    permission_classes = (IsAdminUser,)
    serializer_class = UserIPSerializer
