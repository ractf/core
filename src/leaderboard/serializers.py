"""Serializers for the leaderboard app."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from team.models import Team

from challenge.models import Score


class CTFTimeSerializer(serializers.BaseSerializer):
    """Serializer for getting a scoreboard in a CTFTime compatible format."""

    def to_representation(self, instance):
        """Serialize a team into its name and score."""
        return {"team": instance.name, "score": instance.leaderboard_points}


class LeaderboardTeamScoreSerializer(serializers.ModelSerializer):
    """Serializer for a point on the team score graph."""

    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
        """The fields to serialize."""

        model = Score
        fields = ["points", "timestamp", "team_name", "reason", "metadata"]


class LeaderboardUserScoreSerializer(serializers.ModelSerializer):
    """Serializer for a point on the user score graph."""

    user_name = serializers.ReadOnlyField(source="user.username")

    class Meta:
        """The fields to serialize."""

        model = Score
        fields = ["points", "timestamp", "user_name", "reason", "metadata"]


class TeamPointsSerializer(serializers.ModelSerializer):
    """Serializer for the team leaderboard."""

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["name", "id", "leaderboard_points"]


class UserPointsSerializer(serializers.ModelSerializer):
    """Serializer for the user leaderboard."""

    class Meta:
        """The fields to serialize."""

        model = get_user_model()
        fields = ["username", "id", "leaderboard_points"]


class MatrixSerializer(serializers.ModelSerializer):
    """Serializer for the matrix scoreboard."""

    solve_ids = serializers.SerializerMethodField()

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["id", "name", "leaderboard_points", "solve_ids"]

    def get_solve_ids(self, instance):
        """Return the ids of every challenge a team has solved."""
        return list(instance.solves.values_list("challenge", flat=True))
