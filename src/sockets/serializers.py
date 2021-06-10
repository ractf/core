from rest_framework.serializers import ModelSerializer

from sockets.models import Announcement


class AnnouncementSerializer(ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["id", "body", "title", "timestamp"]
