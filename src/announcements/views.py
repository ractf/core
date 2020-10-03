from rest_framework.viewsets import ModelViewSet

from announcements.models import Announcement
from announcements.serializers import AnnouncementSerializer
from backend.permissions import AdminOrReadOnly


class AnnouncementViewSet(ModelViewSet):
    """
    list:
    Retrieve all announcements.

    create:
    Create a new announcement.

    retrieve:
    Retrieve a specific announcement.

    update:
    Update an announcement.

    partial_update:
    Partially update an announcement.

    destroy:
    Delete an announcement.
    """

    queryset = Announcement.objects.all()
    permission_classes = (AdminOrReadOnly,)
    throttle_scope = "announcement"
    serializer_class = AnnouncementSerializer
    pagination_class = None
