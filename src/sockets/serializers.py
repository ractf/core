"""Serializers used for the sockets app."""

from rest_framework.serializers import ModelSerializer

from sockets.models import Announcement


class AnnouncementSerializer(ModelSerializer):
    """Serializer used for announcements."""

    class Meta:
        """The fields to serialize."""

        model = Announcement
        fields = ["id", "body", "title", "timestamp"]
