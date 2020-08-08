from rest_framework.serializers import ModelSerializer

from announcements.models import Announcement


class AnnouncementSerializer(ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["id", "body", "title", "timestamp"]
