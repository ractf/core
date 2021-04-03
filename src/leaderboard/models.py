from django.db import models
from django.db.models import CASCADE


class Scoreboard(models.Model):
    name = models.CharField(blank=False, null=False, unique=True, max_length=36)


class ScoreboardEntry(models.Model):
    scoreboard = models.ForeignKey(Scoreboard, on_delete=CASCADE)
    team = models.ForeignKey('team.Team', on_delete=CASCADE)
