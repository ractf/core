from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField
from django.db import models
from django.db.models import CASCADE

from backend.validators import NameValidator


class Team(models.Model):
    name = CICharField(max_length=36, unique=True, validators=[NameValidator()])
    is_visible = models.BooleanField(default=True)
    password = models.CharField(max_length=64)
    owner = models.ForeignKey(get_user_model(), on_delete=CASCADE, related_name='owned_team')
    description = models.TextField(blank=True, max_length=400)
    points = models.IntegerField(default=0)
    leaderboard_points = models.IntegerField(default=0)
