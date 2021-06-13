"""API endpoints for the sockets app."""

from rest_framework.viewsets import ModelViewSet

from core.permissions import AdminOrReadOnly
from sockets.models import Announcement
from sockets.serializers import AnnouncementSerializer


class AnnouncementViewSet(ModelViewSet):
    """Viewset for reading and managing announcements."""

    queryset = Announcement.objects.all()
    permission_classes = (AdminOrReadOnly,)
    throttle_scope = "announcement"
    serializer_class = AnnouncementSerializer
    pagination_class = None
