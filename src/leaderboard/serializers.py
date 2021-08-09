from django.contrib.auth import get_user_model
from rest_framework import serializers

from challenge.models import Score
from team.models import Team


class CTFTimeSerializer(serializers.BaseSerializer):
    position: int = 0

    def to_representation(self, instance):
        # TODO: Use SerializerFields for team, score and position.
        return {"team": instance.name, "score": instance.leaderboard_points, "pos": self.get_position(instance)}

    def get_position(self, _) -> int:
        """
        Return an incrementing field representing leaderboard positions.

        This takes an extra argument, representing the model instance,
        for use when it it converted to a SerializerMethodField.
        """
        self.position += 1
        return self.position


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


class MatrixSerializer(serializers.ModelSerializer):
    solve_ids = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "leaderboard_points", "solve_ids"]

    def get_solve_ids(self, instance):
        return list(instance.solves.values_list("challenge", flat=True))
