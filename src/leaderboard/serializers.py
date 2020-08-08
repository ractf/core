from django.contrib.auth import get_user_model
from rest_framework import serializers

from challenge.models import Score
from team.models import Team


class CTFTimeSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return {"team": instance.name, "score": instance.leaderboard_points}


class LeaderboardTeamScoreSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
        model = Score
        fields = ["points", "timestamp", "team_name", "reason", "metadata"]


class LeaderboardUserScoreSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Score
        fields = ["points", "timestamp", "user_name", "reason", "metadata"]


class TeamPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name", "id", "leaderboard_points"]


class UserPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "id", "leaderboard_points"]
