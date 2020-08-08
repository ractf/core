from django.db import models

from team.models import Team


class InviteCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    uses = models.IntegerField(default=0)
    max_uses = models.IntegerField()
    fully_used = models.BooleanField(default=False)
    auto_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
