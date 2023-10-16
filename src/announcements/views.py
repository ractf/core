from backend.viewsets import AuditLoggedViewSet
from rest_framework.viewsets import ModelViewSet

from announcements.models import Announcement
from announcements.serializers import AnnouncementSerializer
from backend.permissions import AdminOrReadOnly


class AnnouncementViewSet(AuditLoggedViewSet, ModelViewSet):
    queryset = Announcement.objects.all()
    permission_classes = (AdminOrReadOnly,)
    throttle_scope = "announcement"
    serializer_class = AnnouncementSerializer
    pagination_class = None
