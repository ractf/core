from rest_framework.viewsets import ModelViewSet

from announcements.models import Announcement
from announcements.serializers import AnnouncementSerializer
from core.permissions import AdminOrReadOnly


class AnnouncementViewSet(ModelViewSet):
    queryset = Announcement.objects.all()
    permission_classes = (AdminOrReadOnly,)
    throttle_scope = "announcement"
    serializer_class = AnnouncementSerializer
    pagination_class = None
