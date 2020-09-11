from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models


class Achievement(models.Model):
    name = models.TextField()
    description = models.TextField()
    metadata = JSONField()
    image_url = models.URLField()
    type = models.TextField()


class UserAchievement(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned = models.BooleanField(default=False)
    progress = models.IntegerField()
