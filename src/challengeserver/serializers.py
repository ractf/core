from rest_framework import serializers


class JobSubmitSerializer(serializers.Serializer):
    challenge_id = serializers.IntegerField()
    job_spec = serializers.JSONField()


class JobSubmitRawSerializer(serializers.Serializer):
    job_spec = serializers.JSONField()
