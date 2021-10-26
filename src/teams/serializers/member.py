"""Serializers for the members app."""

import secrets

from rest_framework import serializers

from challenges.serializers import SolveSerializer
from config import config
from core.mixins import IncorrectSolvesMixin
from teams.models import UserIP, Member
from teams.serializers import MinimalTeamSerializer


class MemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer for Member objects."""

    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        """The fields of the member to serialize."""

        model = Member
        fields = [
            "id",
            "username",
            "is_staff",
            "bio",
            "discord",
            "discordid",
            "state_actor",
            "twitter",
            "reddit",
            "team",
            "points",
            "is_visible",
            "is_active",
            "solves",
            "team_name",
            "leaderboard_points",
            "date_joined",
            "incorrect_solves",
            "is_verified",
        ]


class ListMemberSerializer(serializers.ModelSerializer):
    """Serializer for listing Member objects."""

    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
        """The fields of the member to serialize."""

        model = Member
        fields = ["id", "username", "team", "team_name"]


class AdminMemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer used by admins for Member objects."""

    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        """The fields of the member to serialize."""

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
            "solves",
            "team_name",
            "email",
            "email_verified",
            "leaderboard_points",
            "date_joined",
            "state_actor",
            "incorrect_solves",
            "is_verified",
        ]


class SelfSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    """Serializer used for serializing the current user."""

    solves = SolveSerializer(many=True, read_only=True)
    team = MinimalTeamSerializer(read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    email = serializers.EmailField()
    incorrect_solves = serializers.SerializerMethodField()
    has_2fa = serializers.BooleanField()

    class Meta:
        """The fields to serialize, and which fields should be read only."""

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
            "email",
            "has_2fa",
            "points",
            "solves",
            "team_name",
            "leaderboard_points",
            "date_joined",
            "incorrect_solves",
            "is_verified",
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "team",
            "points",
            "leaderboard_points",
            "date_joined",
            "incorrect_solves",
            "is_verified",
        ]

    def validate_email(self, value):
        """Update email verification token when a user's email is updated."""
        self.instance.email_token = secrets.token_hex()
        self.instance.save()
        return value

    def update(self, instance, validated_data):
        """Update a user's team's name to match their username if teams are disabled."""
        if not config.get("enable_teams"):
            if instance.team:
                instance.team.name = validated_data.get("username", instance.username)
                instance.team.save()
        return super(SelfSerializer, self).update(instance, validated_data)


class UserIPSerializer(serializers.ModelSerializer):
    """Serializer for UserIP objects."""

    class Meta:
        """The fields to serialize."""

        model = UserIP
        fields = ["user", "ip", "seen", "last_seen", "user_agent"]
