"""Database models for the config app."""

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin


class Config(ExportModelOperationsMixin("config"), models.Model):
    """Represents the persisted version of the backed config."""

    key = models.CharField(max_length=64, unique=True)
    value = models.JSONField()
