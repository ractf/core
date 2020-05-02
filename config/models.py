from django.contrib.postgres.fields import JSONField
from django.db import models


class Config(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = JSONField()
