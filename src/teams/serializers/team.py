"""Serializers for team related api endpoints."""

from challenge.serializers import SolveSerializer
from member.serializers import MinimalMemberSerializer
from rest_framework import serializers
from team.models import Team

from core.mixins import IncorrectSolvesMixin
from core.signals import team_create


class SelfTeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer used for the current user's team."""

    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = [
            "id",
            "is_visible",
            "name",
            "password",
            "owner",
            "description",
            "members",
            "solves",
            "incorrect_solves",
            "points",
            "leaderboard_points",
        ]
        read_only_fields = ["id", "is_visible", "incorrect_solves"]


class TeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer used for other users' teams."""

    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        """Which fields to serialize."""

        model = Team
        fields = [
            "id",
            "is_visible",
            "name",
            "owner",
            "description",
            "members",
            "solves",
            "incorrect_solves",
            "points",
            "leaderboard_points",
        ]

    def get_incorrect_solves(self, instance):
        """Get the amount of incorrect solves this team has."""
        return instance.solves.filter(correct=False).count()


class ListTeamSerializer(serializers.ModelSerializer):
    """Team serializer with minimal information."""

    members = serializers.IntegerField(read_only=True, source="members_count")

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["id", "name", "members"]


class AdminTeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer for admins viewing/modifying teams."""

    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = [
            "id",
            "is_visible",
            "name",
            "password",
            "owner",
            "description",
            "members",
            "solves",
            "incorrect_solves",
            "size_limit_exempt",
        ]


class MinimalTeamSerializer(serializers.ModelSerializer):
    """Serializer used for listing teams."""

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["id", "is_visible", "name", "owner", "description"]


class CreateTeamSerializer(serializers.ModelSerializer):
    """Serializer used for team creation."""

    class Meta:
        """The fields to serialize."""

        model = Team
        fields = ["id", "is_visible", "name", "owner", "password"]
        read_only_fields = ["id", "is_visible", "owner"]

    def create(self, validated_data):
        """Create the team and set the owner."""
        name = validated_data["name"]
        password = validated_data["password"]
        team = Team.objects.create(name=name, password=password, owner=self.context["request"].user)
        self.context["request"].user.team = team
        self.context["request"].user.save()
        team_create.send(sender=self.__class__, team=team)
        return team
