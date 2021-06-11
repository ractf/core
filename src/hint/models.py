"""Models for the hint app."""

from django.db import models
from django.db.models import CASCADE, SET_NULL
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin


class Hint(ExportModelOperationsMixin("hint"), models.Model):
    """Represents a hint for a challenge."""

    name = models.CharField(max_length=36)
    challenge = models.ForeignKey("challenge.Challenge", related_name="hint_set", on_delete=CASCADE)
    text = models.TextField()
    penalty = models.IntegerField()


class HintUse(ExportModelOperationsMixin("hint_use"), models.Model):
    """Represents a user/team redeeming a hint."""

    hint = models.ForeignKey("hint.Hint", related_name="uses", on_delete=CASCADE)
    team = models.ForeignKey("team.Team", related_name="hints_used", on_delete=CASCADE, null=True)
    user = models.ForeignKey("member.Member", related_name="hints_used", on_delete=SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    challenge = models.ForeignKey("challenge.Challenge", related_name="hints_used", on_delete=CASCADE)

    class Meta:
        """The constraints on the model."""

        unique_together = (
            "hint",
            "team",
        )
