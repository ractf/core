from django.contrib.auth import get_user_model
from rest_framework import filters
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.schemas.openapi import AutoSchema

from backend.permissions import AdminOrReadOnlyVisible, ReadOnlyBot
from backend.viewsets import AdminListModelViewSet
from member.models import UserIP
from member.serializers import SelfSerializer, MemberSerializer, AdminMemberSerializer, ListMemberSerializer, \
    UserIPSerializer


class SelfView(RetrieveUpdateAPIView):
    """
    get:
    Retrieve the authenticated user.

    put:
    Update the authenticated user.

    patch:
    Partially update the authenticated user.
    """

    serializer_class = SelfSerializer
    permission_classes = (IsAuthenticated & ReadOnlyBot,)
    throttle_scope = 'self'

    def get_object(self):
        UserIP.hook(self.request)
        return get_user_model().objects.prefetch_related('team', 'team__solves', 'team__solves__score',
                                                         'team__hints_used', 'team__solves__challenge',
                                                         'team__solves__solved_by', 'solves',
                                                         'solves__score', 'hints_used', 'solves__challenge',
                                                         'solves__team', 'solves__score__team').distinct()\
            .get(id=self.request.user.id)


class MemberViewSet(AdminListModelViewSet):
    """
    list:
    Retrieve all users.

    create:
    Create a new user.

    retrieve:
    Retrieve a user.

    update:
    Update a user.

    partial_update:
    Partially update a user.

    destroy:
    Delete a user.
    """

    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = 'member'
    serializer_class = MemberSerializer
    admin_serializer_class = AdminMemberSerializer
    list_serializer_class = ListMemberSerializer
    list_admin_serializer_class = ListMemberSerializer
    search_fields = ['username', 'email']
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        if self.action != 'list':
            return get_user_model().objects.prefetch_related('team', 'team__solves', 'team__solves__score',
                                                             'team__hints_used', 'team__solves__challenge',
                                                             'team__solves__solved_by', 'solves',
                                                             'solves__score', 'hints_used', 'solves__challenge',
                                                             'solves__team', 'solves__score__team')
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return get_user_model().objects.order_by('id').prefetch_related('team')
        return get_user_model().objects.filter(is_visible=True).order_by('id').prefetch_related('team')


class UserIPViewSet(ModelViewSet):
    """
    list:
    Retrieve all user IPs.

    create:
    Create a new user IP.

    retrieve:
    Retrieve a specific user IP.

    update:
    Update a user IP.

    partial_update:
    Partially update a user IP.

    destroy:
    Delete a user IP.
    """
    schema = AutoSchema(tags=['userIps'])

    queryset = UserIP.objects.all()
    pagination_class = None
    permission_classes = (IsAdminUser,)
    serializer_class = UserIPSerializer