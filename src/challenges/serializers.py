"""Serializers for the challenge app."""

import serpy
from rest_framework import serializers

from challenges.models import (
    Category,
    Challenge,
    ChallengeFeedback,
    File,
    Score,
    Solve,
    Tag,
)
from challenges.sql import get_negative_votes, get_positive_votes, get_solve_counts
from hint.serializers import FastHintSerializer


def setup_context(context):
    """Add required information such as solve counts to a challenge serialization context."""
    context.update(
        {
            "request": context["request"],
            "solve_counter": get_solve_counts(),
            "votes_positive_counter": get_positive_votes(),
            "votes_negative_counter": get_negative_votes(),
        }
    )
    if context["request"] and context["request"].user is not None:
        if context["request"].user.team is not None:
            context.update(
                {
                    "solves": list(
                        context["request"].user.team.solves.filter(correct=True).values_list("challenge", flat=True)
                    ),
                }
            )


class ForeignAttributeField(serpy.Field):
    """A :class:`Field` that gets a given attribute from a foreign object."""

    def __init__(self, *args, attr_name="id", **kwargs):
        """Construct the field and set the attr_name field."""
        super(ForeignAttributeField, self).__init__(*args, **kwargs)
        self.attr_name = attr_name

    def to_value(self, value):
        """Get the value of this field or None."""
        if value:
            return getattr(value, self.attr_name)
        return None


class DateTimeField(serpy.Field):
    """A :class:`Field` that transforms a datetime into ISO string."""

    def to_value(self, value):
        """Get the value in iso format."""
        return value.isoformat()


class FileSerializer(serializers.ModelSerializer):
    """A serializer for files."""

    class Meta:
        """The fields that should be serialized."""

        model = File
        fields = ["id", "name", "url", "size", "challenge", "md5"]


class FastFileSerializer(serpy.Serializer):
    """A serializer for files that uses serpy for compatibility with other serializers."""

    id = serpy.IntField()
    name = serpy.StrField()
    url = serpy.StrField()
    size = serpy.IntField()
    md5 = serpy.StrField()
    challenge = ForeignAttributeField()


class FastNestedTagSerializer(serpy.Serializer):
    """A serializer for challenge tags."""

    text = serpy.StrField()
    type = serpy.StrField()


class ChallengeSerializerMixin:
    """Utility functions for challenge serializers."""

    def get_unlocked(self, instance):
        """Return if the challenge is unlocked."""
        if not getattr(instance, "unlocked", None):
            return instance.is_unlocked_by(self.context["request"].user, solves=self.context.get("solves", None))
        return instance.unlocked

    def get_solved(self, instance):
        """Return if the challenge is solved."""
        if not getattr(instance, "solved", None):
            return instance.is_solved_by(self.context["request"].user, solves=self.context.get("solves", None))
        return instance.solved

    def get_solve_count(self, instance):
        """Return the solve count of the challenge."""
        return instance.get_solve_count(self.context.get("solve_counter", None))

    def get_unlock_time_surpassed(self, instance):
        """Return if the challenge unlock time is passed, and the challenge can be shown."""
        return instance.unlock_time_surpassed

    def get_votes(self, instance):
        """Return the challenge votes."""
        return {
            "positive": self.context["votes_positive_counter"].get(instance.pk, 0),
            "negative": self.context["votes_negative_counter"].get(instance.pk, 0),
        }

    def get_post_score_explanation(self, instance):
        """Return the challenge explanation, or none if the explanation is not available to the user."""
        if self.get_unlocked(instance):
            return instance.post_score_explanation
        return None


class FastLockedChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    """Serializer used to serialize locked challenges."""

    id = serpy.IntField()
    unlock_requirements = serpy.StrField()
    challenge_metadata = serpy.Field()
    challenge_type = serpy.StrField()
    release_time = DateTimeField()
    unlock_time_surpassed = serpy.MethodField()

    def serialize(self, instance):
        """Serialize the challenge."""
        serialized = self._serialize(instance, self._compiled_fields)
        serialized["challenge_metadata"].pop("cserv_name", None)
        return serialized


class FastChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    """The serpy serializer used to serialize challenges."""

    id = serpy.IntField()
    name = serpy.StrField()
    description = serpy.StrField()
    challenge_type = serpy.StrField()
    challenge_metadata = serpy.Field()
    flag_type = serpy.StrField()
    author = serpy.StrField()
    score = serpy.IntField()
    unlock_requirements = serpy.StrField()
    hints = FastHintSerializer(many=True)
    files = FastFileSerializer(many=True)
    solved = serpy.MethodField()
    unlocked = serpy.MethodField()
    first_blood = ForeignAttributeField(attr_name="username")
    solve_count = serpy.MethodField()
    hidden = serpy.BoolField()
    maintenance = serpy.BoolField()
    votes = serpy.MethodField()
    tags = FastNestedTagSerializer(many=True)
    unlock_time_surpassed = serpy.MethodField()
    post_score_explanation = serpy.StrField()
    tiebreaker = serpy.BoolField()

    def __init__(self, *args, **kwargs) -> None:
        """Add the 'context' attribute to the serializer."""
        super().__init__(*args, **kwargs)

        if "context" in kwargs:
            self.context = kwargs["context"]
            setup_context(self.context)

    def _serialize(self, instance, fields):
        """Serialize a challenge."""
        if (
            instance.is_unlocked_by(self.context["request"].user, solves=self.context.get("solves", None))
            and not instance.hidden
            and instance.unlock_time_surpassed
        ):
            return super(FastChallengeSerializer, self)._serialize(instance, fields)
        return FastLockedChallengeSerializer(instance).serialize(instance)


class FastCategorySerializer(serpy.Serializer):
    """The serpy serializer used to serialize categories."""

    id = serpy.IntField()
    name = serpy.StrField()
    display_order = serpy.StrField()
    contained_type = serpy.StrField()
    description = serpy.StrField()
    metadata = serpy.DictSerializer()
    challenges = serpy.MethodField()

    class Meta:
        """The fields of the category to serialize."""

        model = Category
        fields = ["id", "name", "display_order", "contained_type", "description", "metadata", "challenges"]

    def __init__(self, *args, **kwargs):
        """Construct the serializer and setup the context."""
        super().__init__(*args, **kwargs)
        if "context" in kwargs:
            self.context = kwargs["context"]
            setup_context(self.context)

    def get_challenges(self, instance):
        """Serialize the challenges of a category."""
        return FastChallengeSerializer(instance.challenges, many=True, context=self.context).data


class ChallengeFeedbackSerializer(serializers.ModelSerializer):
    """Serializer used to serialize challenge feedback."""

    class Meta:
        """The fields of the challenge feedback to serialize."""

        model = ChallengeFeedback
        fields = ["id", "challenge", "feedback", "user"]


class CreateCategorySerializer(serializers.ModelSerializer):
    """Serializer used to create a category."""

    class Meta:
        """The fields of the challenge that should be serialized."""

        model = Category
        fields = ["id", "name", "contained_type", "description", "release_time", "metadata"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create a challenge and save it in the database."""
        return Category.objects.create(**validated_data, display_order=Category.objects.count())


class FastAdminChallengeSerializer(ChallengeSerializerMixin, serpy.Serializer):
    """Serpy serializer used to serialize challenges for admins."""

    id = serpy.IntField()
    name = serpy.StrField()
    description = serpy.StrField()
    challenge_type = serpy.StrField()
    challenge_metadata = serpy.Field()
    flag_type = serpy.StrField()
    flag_metadata = serpy.Field()
    author = serpy.StrField()
    score = serpy.IntField()
    unlock_requirements = serpy.StrField()
    hints = FastHintSerializer(many=True)
    files = FastFileSerializer(many=True)
    solved = serpy.MethodField()
    unlocked = serpy.MethodField()
    first_blood = ForeignAttributeField(attr_name="username")
    solve_count = serpy.MethodField()
    hidden = serpy.BoolField()
    maintenance = serpy.BoolField()
    votes = serpy.MethodField()
    tags = FastNestedTagSerializer(many=True)
    unlock_time_surpassed = serpy.MethodField()
    post_score_explanation = serpy.StrField()
    tiebreaker = serpy.BoolField()

    def __init__(self, *args, **kwargs):
        """Construct the serializer and setup the context."""
        super(FastAdminChallengeSerializer, self).__init__(*args, **kwargs)
        if "context" in kwargs:
            self.context = kwargs["context"]
            if "solve_counter" not in self.context:
                setup_context(self.context)

    def serialize(self, instance):
        """Serialize a single challenge."""
        return super(
            FastAdminChallengeSerializer, FastAdminChallengeSerializer(instance, context=self.context)
        ).to_value(instance)

    def to_value(self, instance):
        """Serialize a challenge or a list of challenges."""
        if self.many:
            return [self.serialize(o) for o in instance]
        return self.serialize(instance)


class CreateChallengeSerializer(serializers.ModelSerializer):
    """Serializer used when an admin creates a challenge."""

    tags = serializers.ListField(write_only=True)

    class Meta:
        """The fields of the challenge model that should me serialized."""

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
            "maintenance",
            "release_time",
            "post_score_explanation",
            "tags",
            "tiebreaker",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create a challenge instance."""
        tags = validated_data.pop("tags", [])
        challenge = Challenge.objects.create(**validated_data)
        for tag_data in tags:
            Tag.objects.create(challenge=challenge, **tag_data)
        return challenge

    def update(self, instance, validated_data):
        """Update a challenge instance."""
        tags = validated_data.pop("tags", None)
        if tags:
            Tag.objects.filter(challenge=instance).delete()
            for tag_data in tags:
                Tag.objects.create(challenge=instance, **tag_data)
        return super().update(instance, validated_data)


class FastAdminCategorySerializer(serpy.Serializer):
    """Serializer for Categories used when admins access the endpoint."""

    id = serpy.IntField()
    name = serpy.StrField()
    display_order = serpy.StrField()
    contained_type = serpy.StrField()
    description = serpy.StrField()
    metadata = serpy.DictSerializer()
    challenges = serpy.MethodField()

    def __init__(self, *args, **kwargs):
        """Construct the serializer and setup the context."""
        super().__init__(*args, **kwargs)
        if "context" in kwargs:
            self.context = kwargs["context"]
            setup_context(self.context)

    def get_challenges(self, instance):
        """Return a seralized list of all challenges for this category."""
        return FastAdminChallengeSerializer(instance.challenges, many=True, context=self.context).data


class AdminScoreSerializer(serializers.ModelSerializer):
    """Serializer for Solve objects, used for creating or modifying solves."""

    class Meta:
        """The fields of the score model that should me serialized."""

        model = Score
        fields = ["team", "user", "reason", "points", "penalty", "leaderboard", "timestamp", "metadata"]


class SolveSerializer(serializers.ModelSerializer):
    """Serializer for Solve objects."""

    team_name = serializers.ReadOnlyField(source="team.name")
    solved_by_name = serializers.ReadOnlyField(source="solved_by.username")
    challenge_name = serializers.ReadOnlyField(source="challenge.name")
    points = serializers.SerializerMethodField()
    scored = serializers.SerializerMethodField()

    class Meta:
        """The fields of the solve model that should me serialized."""

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
        """Serialize the solve if it is correct, else return None."""
        if instance.correct:
            return super(SolveSerializer, self).to_representation(instance)
        return None

    def get_points(self, instance):
        """Return how many points the solve is worth after penalties."""
        if instance.correct and instance.score is not None:
            return instance.score.points - instance.score.penalty
        return 0

    def get_scored(self, instance):
        """Return True if the solve should count towards a users displayed leaderboard points."""
        if instance.correct and instance.score is not None:
            return instance.score.leaderboard
        return False


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag objects."""

    class Meta:
        """Which classes and fields should be serialized for each Tag."""

        model = Tag
        fields = ["id", "challenge", "text", "type", "post_competition"]
