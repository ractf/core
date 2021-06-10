from django.db import models
from django_prometheus.models import ExportModelOperationsMixin


class Config(ExportModelOperationsMixin("config"), models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.JSONField()
