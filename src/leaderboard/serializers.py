"""Serializers for the leaderboard app."""

from rest_framework import serializers

from challenges.models import Score
from teams.models import Team, Member


class CTFTimeSerializer(serializers.BaseSerializer):
    """Serializer for getting a scoreboard in a CTFTime compatible format."""

    position: int = 0

    def to_representation(self, instance):
        """Serialize a team into its name and score."""
        # TODO: Use SerializerFields for team, score and position.
        return {"team": instance.name, "score": instance.leaderboard_points, "pos": self.get_position(instance)}

    def get_position(self, _) -> int:
        """Return an incrementing field representing leaderboard positions."""
        self.position += 1
        return self.position


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

        model = Member
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
