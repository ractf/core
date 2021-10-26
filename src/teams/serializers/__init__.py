"""Serializers used for teams and their members."""

from rest_framework import serializers

from teams.models import Member, Team


class MinimalTeamSerializer(serializers.ModelSerializer):
    """Serializer used for listing teams."""

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["id", "is_visible", "name", "owner", "description"]


class MinimalMemberSerializer(serializers.ModelSerializer):
    """Serializer for members that includes minimal detail."""

    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
        """The fields to serialize."""

        model = Member
        fields = [
            "id",
            "username",
            "is_staff",
            "bio",
            "discord",
            "discordid",
            "twitter",
            "reddit",
            "team",
            "points",
            "is_visible",
            "is_active",
            "team_name",
            "leaderboard_points",
            "state_actor",
            "date_joined",
            "is_verified",
        ]
