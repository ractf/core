from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from team.models import Team


class InviteCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    uses = models.IntegerField(default=0)
    max_uses = models.IntegerField()
    fully_used = models.BooleanField(default=False)
    auto_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)


def one_day():
    return timezone.now() + timedelta(days=1)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    issued = models.DateTimeField(default=timezone.now)
    expires = models.DateTimeField(default=one_day)
