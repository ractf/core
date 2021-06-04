from collections import Counter

import serpy
from rest_framework import serializers

from challenge.models import Challenge, Category, File, Solve, Score, ChallengeFeedback, Tag, ChallengeVote
from challenge.sql import get_solve_counts, get_positive_votes, get_negative_votes
from hint.serializers import HintSerializer, FastHintSerializer


def setup_context(context):
    context.update({
        "request": context["request"],
        "solve_counter": get_solve_counts(),
        "votes_positive_counter": get_positive_votes(),
        "votes_negative_counter": get_negative_votes(),
    })
    if context["request"].user.team is not None:
        context.update({
            "solves": list(
                context["request"].user.team.solves.filter(correct=True).values_list("challenge", flat=True)
            ),
        })


class ForeignKeyField(serpy.Field):
    """A :class:`Field` that gets a given attribute from a foreign object."""
    def __init__(self, *args, attr_name="id", **kwargs):
        super(ForeignKeyField, self).__init__(*args, **kwargs)
        self.attr_name = attr_name

    def to_value(self, value):
        if value:
            return getattr(value, self.attr_name)
        return None


class DateTimeField(serpy.Field):
    """A :class:`Field` that transforms a datetime into ISO string."""
    def to_value(self, value):
        return value.isoformat()


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "name", "url", "size", "challenge", "md5"]


class FastFileSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    url = serpy.StrField()
    size = serpy.IntField()
    md5 = serpy.StrField()
    challenge = ForeignKeyField()


class NestedTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["text", "type"]


class FastNestedTagSerializer(serpy.Serializer):
    text = serpy.StrField()
    type = serpy.StrField()


class ChallengeSerializerMixin:
    def get_unlocked(self, instance):
        if not getattr(instance, "unlocked", None):
            return instance.is_unlocked(self.context["request"].user, solves=self.context.get("solves", None))
        return instance.unlocked

    def get_solved(self, instance):
        if not getattr(instance, "solved", None):
            return instance.is_solved(self.context["request"].user, solves=self.context.get("solves", None))
        return instance.solved

    def get_solve_count(self, instance):
        return instance.get_solve_count(self.context.get("solve_counter", None))

    def get_unlock_time_surpassed(self, instance):
        return instance.unlock_time_surpassed

    def get_votes(self, instance):
        return {
            "positive": self.context["votes_positive_counter"].get(instance.id, 0),
            "negative": self.context["votes_negative_counter"].get(instance.id, 0)
        }

    def get_post_score_explanation(self, instance):
        if self.get_unlocked(instance):
            return instance.post_score_explanation
        return None


class FastLockedChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    id = serpy.IntField()
    unlock_requirements = serpy.StrField()
    challenge_metadata = serpy.DictSerializer()
    challenge_type = serpy.StrField()
    release_time = DateTimeField()
    unlock_time_surpassed = serpy.MethodField()


class FastChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    description = serpy.StrField()
    challenge_type = serpy.StrField()
    flag_type = serpy.StrField()
    author = serpy.StrField()
    score = serpy.IntField()
    unlock_requirements = serpy.StrField()
    hints = FastHintSerializer(many=True)
    files = FastFileSerializer(many=True)
    solved = serpy.MethodField()
    unlocked = serpy.MethodField()
    first_blood = ForeignKeyField()
    solve_count = serpy.MethodField()
    hidden = serpy.BoolField()
    votes = serpy.MethodField()
    tags = FastNestedTagSerializer(many=True)
    unlock_time_surpassed = serpy.MethodField()
    post_score_explanation = serpy.StrField()


class LockedChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    unlock_time_surpassed = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'unlock_requirements', 'challenge_metadata', 'challenge_type', 'hidden',
                  'unlock_time_surpassed', 'release_time']


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


class LockedChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    unlock_time_surpassed = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "unlock_requirements",
            "challenge_metadata",
            "challenge_type",
            "hidden",
            "unlock_time_surpassed",
            "release_time",
            "score"
        ]


    def __init__(self, *args, **kwargs):
        super(FastChallengeSerializer, self).__init__(*args, **kwargs)
        if 'context' in kwargs:
            self.context = kwargs['context']
            if 'solve_counter' not in self.context:
                setup_context(self.context)

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'category', 'description', 'challenge_type', 'challenge_metadata', 'flag_type',
                  'author', 'auto_unlock', 'score', 'unlock_requirements', 'hints', 'files', 'solved', 'unlocked',
                  'first_blood', 'first_blood_name', 'solve_count', 'hidden', 'votes', 'tags', 'unlock_time_surpassed',
                  'post_score_explanation']

    class Meta:
        model = Challenge
        fields = [
            "id",
            "name",
            "category",
            "description",
            "challenge_type",
            "challenge_metadata",
            "flag_type",
            "author",
            "score",
            "unlock_requirements",
            "hints",
            "files",
            "solved",
            "unlocked",
            "first_blood",
            "first_blood_name",
            "solve_count",
            "hidden",
            "votes",
            "tags",
            "unlock_time_surpassed",
            "post_score_explanation",
        ]

    def serialize(self, instance):
        if instance.is_unlocked(self.context["request"].user, solves=self.context.get("solves", None)) and \
                not instance.hidden and instance.unlock_time_surpassed:
            return super(FastChallengeSerializer, FastChallengeSerializer(instance, context=self.context)).to_value(instance)
        return FastLockedChallengeSerializer(instance).data

    def to_representation(self, instance):
        if (
            instance.is_unlocked(self.context["request"].user, solves=self.context.get("solves", None))
            and not instance.hidden
            and instance.unlock_time_surpassed
        ):
            return super(ChallengeSerializer, self).to_representation(instance)
        return LockedChallengeSerializer(instance).to_representation(instance)

    def to_value(self, instance):
        if self.many:
            return [self.serialize(o) for o in instance]
        return self.serialize(instance)


class FastCategorySerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    display_order = serpy.StrField()
    contained_type = serpy.StrField()
    description = serpy.StrField()
    metadata = serpy.DictSerializer()
    challenges = serpy.MethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "display_order", "contained_type", "description", "metadata", "challenges"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "context" in kwargs:
            self.context = kwargs["context"]
            setup_context(self.context)

    def get_challenges(self, instance):
        return FastChallengeSerializer(instance.challenges, many=True, context=self.context).data


class ChallengeFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeFeedback
        fields = ["id", "challenge", "feedback", "user"]


class CreateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "contained_type", "description", "release_time", "metadata"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return Category.objects.create(**validated_data, display_order=Category.objects.count())


class FastAdminChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    description = serpy.StrField()
    challenge_type = serpy.StrField()
    flag_type = serpy.StrField()
    author = serpy.StrField()
    score = serpy.IntField()
    unlock_requirements = serpy.StrField()
    hints = FastHintSerializer(many=True)
    files = FastFileSerializer(many=True)
    solved = serpy.MethodField()
    unlocked = serpy.MethodField()
    first_blood = ForeignKeyField()
    solve_count = serpy.MethodField()
    hidden = serpy.BoolField()
    votes = serpy.MethodField()
    tags = FastNestedTagSerializer(many=True)
    unlock_time_surpassed = serpy.MethodField()
    post_score_explanation = serpy.StrField()

    def __init__(self, *args, **kwargs):
        super(FastAdminChallengeSerializer, self).__init__(*args, **kwargs)
        if 'context' in kwargs:
            self.context = kwargs['context']
            if 'solve_counter' not in self.context:
                setup_context(self.context)

    def serialize(self, instance):
        return super(FastAdminChallengeSerializer, FastAdminChallengeSerializer(instance, context=self.context))\
            .to_value(instance)

    def to_value(self, instance):
        if self.many:
            return [self.serialize(o) for o in instance]
        return self.serialize(instance)


class AdminChallengeSerializer(ChallengeSerializerMixin, serializers.ModelSerializer):
    hints = HintSerializer(many=True, read_only=True)
    files = FileSerializer(many=True, read_only=True)
    solved = serializers.SerializerMethodField()
    unlocked = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    first_blood_name = serializers.ReadOnlyField(source="first_blood.team.name")
    solve_count = serializers.SerializerMethodField()
    tags = NestedTagSerializer(many=True, read_only=False)

    class Meta:
        model = Challenge
        fields = [
            "id",
            "name",
            "category",
            "description",
            "challenge_type",
            "challenge_metadata",
            "flag_type",
            "author",
            "score",
            "unlock_requirements",
            "flag_metadata",
            "hints",
            "files",
            "solved",
            "unlocked",
            "first_blood",
            "first_blood_name",
            "solve_count",
            "hidden",
            "release_time",
            "votes",
            "post_score_explanation",
            "tags",
        ]


class CreateChallengeSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(write_only=True)

    class Meta:
        model = Challenge
        fields = [
            "id",
            "name",
            "category",
            "description",
            "challenge_type",
            "challenge_metadata",
            "flag_type",
            "author",
            "score",
            "unlock_requirements",
            "flag_metadata",
            "hidden",
            "release_time",
            "post_score_explanation",
            "tags",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        challenge = Challenge.objects.create(**validated_data)
        for tag_data in tags:
            Tag.objects.create(challenge=challenge, **tag_data)
        return challenge

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        if tags:
            Tag.objects.filter(challenge=instance).delete()
            for tag_data in tags:
                Tag.objects.create(challenge=instance, **tag_data)
        return super().update(instance, validated_data)


class AdminCategorySerializer(serializers.ModelSerializer):
    challenges = AdminChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "display_order",
            "contained_type",
            "description",
            "metadata",
            "challenges",
            "release_time",
        ]


class FastAdminCategorySerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    display_order = serpy.StrField()
    contained_type = serpy.StrField()
    description = serpy.StrField()
    metadata = serpy.DictSerializer()
    challenges = serpy.MethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "context" in kwargs:
            self.context = kwargs["context"]
            setup_context(self.context)

    def get_challenges(self, instance):
        return FastAdminChallengeSerializer(instance.challenges, many=True, context=self.context).data


class AdminScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = ["team", "user", "reason", "points", "penalty", "leaderboard", "timestamp", "metadata"]


class SolveSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source="team.name")
    solved_by_name = serializers.ReadOnlyField(source="solved_by.username")
    challenge_name = serializers.ReadOnlyField(source="challenge.name")
    points = serializers.SerializerMethodField()
    scored = serializers.SerializerMethodField()

    class Meta:
        model = Solve
        fields = [
            "id",
            "team",
            "challenge",
            "points",
            "solved_by",
            "first_blood",
            "timestamp",
            "scored",
            "team_name",
            "solved_by_name",
            "challenge_name",
        ]

    def to_representation(self, instance):
        if instance.correct:
            return super(SolveSerializer, self).to_representation(instance)
        return None

    def get_points(self, instance):
        if instance.correct and instance.score is not None:
            return instance.score.points - instance.score.penalty
        return 0

    def get_scored(self, instance):
        if instance.correct and instance.score is not None:
            return instance.score.leaderboard
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "challenge", "text", "type", "post_competition"]
