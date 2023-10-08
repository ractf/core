from django.db.utils import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST

from backend.exceptions import FormattedException
from backend.mixins import IncorrectSolvesMixin
from backend.signals import team_create
from challenge.serializers import SolveSerializer
from member.serializers import MinimalMemberSerializer
from team.models import Team, LeaderboardGroup


class SelfTeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
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
            "leaderboard_group"
        ]
        read_only_fields = ["id", "is_visible", "incorrect_solves", "leaderboard_group"]


class TeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
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
            "leaderboard_group"
        ]

    def get_incorrect_solves(self, instance):
        return instance.solves.filter(correct=False).count()


class ListTeamSerializer(serializers.ModelSerializer):
    members = serializers.IntegerField(read_only=True, source="members_count")

    class Meta:
        model = Team
        fields = ["id", "name", "members", "leaderboard_group"]


class LeaderboardGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardGroup
        fields = ["id", "name", "description", "is_self_assignable", "has_own_leaderboard"]


class AdminTeamSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    members = MinimalMemberSerializer(many=True, read_only=True)
    solves = SolveSerializer(many=True, read_only=True)
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
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
            "points",
            "leaderboard_points",
            "leaderboard_group"
        ]


class MinimalTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "is_visible", "name", "owner", "description"]


class CreateTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "is_visible", "name", "owner", "password", "leaderboard_group"]
        read_only_fields = ["id", "is_visible", "owner"]

    def create(self, validated_data):
        try:
            name = validated_data["name"]
            password = validated_data["password"]
            leaderboard_group = validated_data.get("leaderboard_group", None)

            if leaderboard_group is not None and not leaderboard_group.is_self_assignable:
                raise ValidationError("illegal_leaderboard_group")

            team = Team.objects.create(
                name=name,
                password=password,
                owner=self.context["request"].user,
                leaderboard_group=leaderboard_group
            )

            self.context["request"].user.team = team
            self.context["request"].user.save()
            team_create.send(sender=self.__class__, team=team)
            return team
        except IntegrityError:
            raise ValidationError("team_name_in_use")
