from rest_framework import serializers

from challenge.models import Challenge, Category, File, Solve, ChallengeVote
from hint.serializers import HintSerializer


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'name', 'url', 'size', 'challenge']


class LockedChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['id', 'unlocks', 'challenge_metadata', 'challenge_type', 'hidden']


class ChallengeSerializerMixin:
    def get_unlocked(self, instance):
        return instance.unlocked

    def get_solved(self, instance):
        return instance.solved

    def get_solve_count(self, instance):
        return instance.solve_count

    def get_votes(self, instance):
        votes = ChallengeVote.objects.filter(challenge=instance)
        positive = votes.filter(positive=True).count()
        negative = votes.filter(positive=False).count()
        self_vote = votes.filter(user=self.context['request'].user).first()
        return {
            "positive": positive,
            "negative": negative,
            "self": self_vote.positive if self_vote else None
        }


class ChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    hints = HintSerializer(many=True, read_only=True)
    files = FileSerializer(many=True, read_only=True)
    solved = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    first_blood_name = serializers.ReadOnlyField(source='first_blood.username')
    solve_count = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'hints', 'files', 'solved', 'unlocked', 'first_blood',
                  'first_blood_name', 'solve_count', 'hidden', 'votes']

    def to_representation(self, instance):
        if instance.unlocked and not instance.hidden:
            return super(ChallengeSerializer, self).to_representation(instance)
        return LockedChallengeSerializer(instance).to_representation(instance)


class CategorySerializer(serializers.ModelSerializer):
    challenges = ChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'contained_type', 'description', 'metadata', 'challenges']


class CreateCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'contained_type', 'description', 'release_time']
        read_only_fields = ['id']

    def create(self, validated_data):
        name = validated_data['name']
        contained_type = validated_data['contained_type']
        description = validated_data['description']
        return Category.objects.create(name=name, contained_type=contained_type, description=description,
                                       display_order=Category.objects.count())


class AdminChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    hints = HintSerializer(many=True, read_only=True)
    files = FileSerializer(many=True, read_only=True)
    solved = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    first_blood_name = serializers.ReadOnlyField(source='first_blood.team.name')
    solve_count = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'flag_metadata', 'hints', 'files', 'solved',
                  'unlocked', 'first_blood', 'first_blood_name', 'solve_count', 'hidden', 'release_time', 'votes']


class CreateChallengeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'flag_metadata', 'hidden', 'release_time',
                  'post_score_explanation']
        read_only_fields = ['id']


class AdminCategorySerializer(serializers.ModelSerializer):
    challenges = AdminChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'contained_type', 'description', 'metadata', 'challenges',
                  'release_time']


class SolveSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source='team.name')
    solved_by_name = serializers.ReadOnlyField(source='solved_by.username')
    challenge_name = serializers.ReadOnlyField(source='challenge.name')
    points = serializers.SerializerMethodField()
    scored = serializers.SerializerMethodField()

    class Meta:
        model = Solve
        fields = ['id', 'team', 'challenge', 'points', 'solved_by', 'first_blood', 'timestamp', 'scored', 'team_name',
                  'solved_by_name', 'challenge_name']

    def to_representation(self, instance):
        if instance.correct:
            return super(SolveSerializer, self).to_representation(instance)
        return None

    def get_points(self, instance):
        if instance.correct:
            return instance.score.points - instance.score.penalty
        return 0

    def get_scored(self, instance):
        if instance.correct:
            return instance.score.leaderboard
        return False
