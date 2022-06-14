import secrets

from rest_framework import serializers

from backend.mixins import IncorrectSolvesMixin
from challenge.serializers import SolveSerializer
from config import config
from member.models import UserIP, Member


class MemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
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
    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
        model = Member
        fields = ["id", "username", "team", "team_name"]


class AdminMemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
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


class MinimalMemberSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source="team.name")

    class Meta:
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


class SelfSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    from team.serializers import MinimalTeamSerializer

    solves = SolveSerializer(many=True, read_only=True)
    team = MinimalTeamSerializer(read_only=True)
    team_name = serializers.ReadOnlyField(source="team.name")
    email = serializers.EmailField()
    incorrect_solves = serializers.SerializerMethodField()
    has_2fa = serializers.BooleanField()

    class Meta:
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
        self.instance.email_token = secrets.token_hex()
        self.instance.save()
        return value

    def update(self, instance, validated_data):
        if not config.get("enable_teams"):
            if instance.team:
                instance.team.name = validated_data.get("username", instance.username)
                instance.team.save()
        return super(SelfSerializer, self).update(instance, validated_data)


class UserIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserIP
        fields = ["user", "ip", "seen", "last_seen", "user_agent"]
