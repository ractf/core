from django.db import models
from django.db.models import CASCADE, SET_NULL
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from challenge.models import Challenge
from member.models import Member
from team.models import Team


class Hint(ExportModelOperationsMixin("hint"), models.Model):
    name = models.CharField(max_length=36)
    challenge = models.ForeignKey(Challenge, related_name="hint_set", on_delete=CASCADE)
    text = models.TextField()
    penalty = models.IntegerField()


class HintUse(ExportModelOperationsMixin("hint_use"), models.Model):
    hint = models.ForeignKey(Hint, related_name="uses", on_delete=CASCADE)
    team = models.ForeignKey(Team, related_name="hints_used", on_delete=CASCADE, null=True)
    user = models.ForeignKey(Member, related_name="hints_used", on_delete=SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    challenge = models.ForeignKey(Challenge, related_name="hints_used", on_delete=CASCADE)

    class Meta:
        unique_together = (
            "hint",
            "team",
        )
