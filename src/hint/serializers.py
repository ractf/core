"""Serializers for the hint app."""

import serpy
from rest_framework import serializers

from hint.models import Hint, HintUse


def is_used(context, instance):
    """Return True if a user can view a hint."""
    return (
        context["request"].user.team is not None
        and context["request"].user.team.hints_used.filter(hint=instance).exists()
    )


class HintUseSerializer(serializers.ModelSerializer):
    """Serializer for a hint use."""

    class Meta:
        """The fields that should be serialized for a hint use."""

        model = HintUse
        fields = ["id", "hint", "team", "user", "timestamp"]


class HintSerializerMixin:
    """Common functions for hint-related serializers."""

    def get_text(self, instance):
        """Get the text of a hint or an empty string if the hint is locked."""
        if (self.context["request"].user.is_staff and not self.context["request"].user.should_deny_admin()) or is_used(
            self.context, instance
        ):
            return instance.text
        else:
            return ""

    def get_used(self, instance):
        """Return True if the hint is used."""
        return is_used(self.context, instance)


class HintSerializer(serializers.ModelSerializer, HintSerializerMixin):
    """Serializer for the Hint model."""

    text = serializers.SerializerMethodField()
    used = serializers.SerializerMethodField()

    class Meta:
        """The fields that should be serialized."""

        model = Hint
        fields = ["id", "name", "penalty", "challenge", "text", "used"]


class FastHintSerializer(serpy.Serializer):
    """Serpy serializer for hints."""

    id = serpy.IntField()
    name = serpy.StrField()
    penalty = serpy.IntField()
    text = serpy.StrField()
    used = serpy.BoolField()


class CreateHintSerializer(serializers.ModelSerializer):
    """Serializer for creating hints."""

    class Meta:
        """The fields that should be serialized."""

        model = Hint
        fields = ["id", "name", "penalty", "challenge", "text"]
        read_only_fields = ["id"]


class FullHintSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a hint."""

    used = serializers.SerializerMethodField()

    class Meta:
        """The fields that should be serialized."""

        model = Hint
        fields = ["id", "name", "penalty", "challenge", "text", "used"]

    def get_used(self, instance):
        """Return True if the hint is used."""
        return is_used(self.context, instance)


class UseHintSerializer(serializers.Serializer):
    """Serializer for the HintUse model."""

    id = serializers.IntegerField()
