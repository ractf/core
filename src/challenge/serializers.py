from rest_framework import serializers

from challenge.models import Challenge, Category, File, Solve, ChallengeVote, ChallengeFeedback, Tag
from hint.serializers import HintSerializer


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'name', 'url', 'size', 'challenge', 'md5']


class NestedTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['text', 'type']


class ChallengeSerializerMixin:
    def get_unlocked(self, instance):
        return instance.unlocked

    def get_solved(self, instance):
        return instance.solved

    def get_solve_count(self, instance):
        return instance.solve_count

    def get_unlock_time_surpassed(self, instance):
        return instance.unlock_time_surpassed

    def get_votes(self, instance):
        return {
            "positive": instance.votes_positive,
            "negative": instance.votes_negative
        }

    def get_post_score_explanation(self, instance):
        if instance.solved:
            return instance.post_score_explanation
        return None


class LockedChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    unlock_time_surpassed = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'unlocks', 'challenge_metadata', 'challenge_type', 'hidden', 'unlock_time_surpassed',
                  'release_time']


class ChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    hints = HintSerializer(many=True, read_only=True)
    files = FileSerializer(many=True, read_only=True)
    solved = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()
    unlock_time_surpassed = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    first_blood_name = serializers.ReadOnlyField(source='first_blood.username')
    solve_count = serializers.SerializerMethodField()
    tags = NestedTagSerializer(many=True, read_only=True)
    post_score_explanation = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'hints', 'files', 'solved', 'unlocked', 'first_blood',
                  'first_blood_name', 'solve_count', 'hidden', 'votes', 'tags', 'unlock_time_surpassed',
                  'post_score_explanation']

    def to_representation(self, instance):
        if instance.unlocked and not instance.hidden and instance.unlock_time_surpassed:
            return super(ChallengeSerializer, self).to_representation(instance)
        return LockedChallengeSerializer(instance).to_representation(instance)


class CategorySerializer(serializers.ModelSerializer):
    challenges = ChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'contained_type', 'description', 'metadata', 'challenges']


class ChallengeFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeFeedback
        fields = ['id', 'challenge', 'feedback', 'user']


class CreateCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'contained_type', 'description', 'release_time', 'metadata']
        read_only_fields = ['id']

    def create(self, validated_data):
        return Category.objects.create(**validated_data, display_order=Category.objects.count())


class AdminChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    hints = HintSerializer(many=True, read_only=True)
    files = FileSerializer(many=True, read_only=True)
    solved = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    first_blood_name = serializers.ReadOnlyField(source='first_blood.team.name')
    solve_count = serializers.SerializerMethodField()
    tags = NestedTagSerializer(many=True, read_only=False)

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'flag_metadata', 'hints', 'files', 'solved',
                  'unlocked', 'first_blood', 'first_blood_name', 'solve_count', 'hidden', 'release_time', 'votes',
                  'post_score_explanation', 'tags']


class CreateChallengeSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(write_only=True)

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlocks', 'flag_metadata', 'hidden', 'release_time',
                  'post_score_explanation', 'tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        unlocks = validated_data.pop('unlocks', [])
        challenge = Challenge.objects.create(**validated_data)
        challenge.unlocks.set(unlocks)
        for tag_data in tags:
            Tag.objects.create(challenge=challenge, **tag_data)
        return challenge

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags:
            Tag.objects.filter(challenge=instance).delete()
            for tag_data in tags:
                Tag.objects.create(challenge=instance, **tag_data)
        return super().update(instance, validated_data)


class AdminCategorySerializer(serializers.ModelSerializer):
    challenges = AdminChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_order', 'contained_type', 'description', 'metadata', 'challenges',
                  'release_time']


class AdminSolveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solve
        fields = ['team', 'challenge', 'solved_by', 'first_blood', 'timestamp', 'correct', 'flag', 'score']


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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'challenge', 'text', 'type', 'post_competition']
