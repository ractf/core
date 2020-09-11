from rest_framework.serializers import ModelSerializer

from achievements.models import Achievement, UserAchievement


class AchievementSerializer(ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["name", "description", "metadata", "image_url", "type"]


class UserAchievementSerializer(ModelSerializer):
    class Meta:
        model = UserAchievement
        fields = ["achievement", "earned", "progress"]
