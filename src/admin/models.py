import os

from django.db import models
from django.db.models import SET_NULL

from member.models import Member


class AuditLogEntry(models.Model):
    user = models.ForeignKey(Member, null=True, on_delete=SET_NULL)
    username = models.CharField(max_length=255)
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    extra = models.JSONField()

    @classmethod
    def create_management_entry(cls, command: str, extra=None):
        AuditLogEntry.objects.create(user=None, username=f"System ({os.getlogin()})",
                                     action=f"management_{command}", extra=extra)

    @classmethod
    def create_entry(cls, user: Member, action: str, extra=None):
        AuditLogEntry.objects.create(user=user, username=user.username, action=action, extra=extra)
