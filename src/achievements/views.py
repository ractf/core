from rest_framework.viewsets import ModelViewSet

from achievements.models import Achievement
from achievements.serializers import AchievementSerializer
from backend.permissions import AdminOrReadOnly


class AchievementViewSet(ModelViewSet):
    queryset = Achievement.objects.all()
    permission_classes = (AdminOrReadOnly,)
    serializer_class = AchievementSerializer
    pagination_class = None
