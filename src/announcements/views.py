from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet

from announcements.models import Announcement
from announcements.serializers import AnnouncementSerializer
from backend.permissions import Admin, ReadOnly


class AnnouncementViewSet(ModelViewSet):
    queryset = Announcement.objects.all()
    permission_classes = (DjangoModelPermissions | Admin | ReadOnly,)
    throttle_scope = "announcement"
    serializer_class = AnnouncementSerializer
    pagination_class = None
