from django.contrib.auth import get_user_model
from rest_framework import filters
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from backend.permissions import AdminOrReadOnlyVisible
from backend.viewsets import AdminListModelViewSet
from member.serializers import SelfSerializer, MemberSerializer, AdminMemberSerializer, ListMemberSerializer


class SelfView(RetrieveUpdateAPIView):
    serializer_class = SelfSerializer
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'self'

    def get_object(self):
        return get_user_model().objects.prefetch_related('team', 'team__solves', 'team__solves__score',
                                                         'team__hints_used', 'team__solves__challenge',
                                                         'team__solves__solved_by', 'solves',
                                                         'solves__score', 'hints_used', 'solves__challenge',
                                                         'solves__team', 'solves__score__team').get(id=self.request.user.id)


class MemberViewSet(AdminListModelViewSet):
    permission_classes = (AdminOrReadOnlyVisible,)
    throttle_scope = 'member'
    serializer_class = MemberSerializer
    admin_serializer_class = AdminMemberSerializer
    list_serializer_class = ListMemberSerializer
    list_admin_serializer_class = ListMemberSerializer
    search_fields = ['username']
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
