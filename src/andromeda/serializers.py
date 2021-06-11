"""Serializers for the andromeda integration"""

from rest_framework import serializers


class JobSubmitSerializer(serializers.Serializer):
    """Serializer for job submissions associated with a challenge id."""

    challenge_id = serializers.IntegerField()
    job_spec = serializers.JSONField()


class JobSubmitRawSerializer(serializers.Serializer):
    """Serializer for job submissions."""

    job_spec = serializers.JSONField()
