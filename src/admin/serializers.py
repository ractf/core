from rest_framework import serializers

from admin.models import AuditLogEntry


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = ["user", "username", "action", "time", "extra"]
