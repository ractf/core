import secrets

from django.contrib.auth import get_user_model
from rest_framework import serializers

from backend.mixins import IncorrectSolvesMixin
from challenge.serializers import SolveSerializer
from member.models import UserIP


class MemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source='team.name')
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'is_staff', 'bio', 'discord', 'discordid', 'twitter', 'reddit', 'team',
                  'points', 'is_visible', 'is_active', 'solves', 'team_name', 'leaderboard_points', 'date_joined',
                  'incorrect_solves']


class ListMemberSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source='team.name')

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'team', 'team_name']


class AdminMemberSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    solves = SolveSerializer(many=True, read_only=True)
    team_name = serializers.ReadOnlyField(source='team.name')
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'is_staff', 'bio', 'discord', 'discordid', 'twitter', 'reddit', 'team',
                  'points', 'is_visible', 'is_active', 'solves', 'team_name', 'email', 'email_verified',
                  'leaderboard_points', 'date_joined', 'incorrect_solves']


class MinimalMemberSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source='team.name')

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'is_staff', 'bio', 'discord', 'discordid', 'twitter', 'reddit', 'team',
                  'points', 'is_visible', 'is_active', 'team_name', 'leaderboard_points', 'date_joined']


class SelfSerializer(IncorrectSolvesMixin, serializers.ModelSerializer):
    from team.serializers import MinimalTeamSerializer
    solves = SolveSerializer(many=True, read_only=True)
    team = MinimalTeamSerializer(read_only=True)
    team_name = serializers.ReadOnlyField(source='team.name')
    email = serializers.EmailField()
    incorrect_solves = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'is_staff', 'bio', 'discord', 'discordid', 'twitter', 'reddit', 'team', 'email',
                  'totp_status', 'points', 'solves', 'team_name', 'leaderboard_points', 'date_joined',
                  'incorrect_solves']
        read_only_fields = ['id', 'is_staff', 'team', 'email', 'totp_status', 'points',
                            'leaderboard_points', 'date_joined', 'incorrect_solves']

    def validate_email(self, value):
        self.instance.password_reset_token = secrets.token_hex()
        self.instance.email_token = secrets.token_hex()
        self.instance.save()
        return value


class UserIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserIP
        fields = ['user', 'ip', 'seen', 'last_seen', 'user_agent']