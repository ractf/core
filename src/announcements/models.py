from django.db import models
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin


class Announcement(ExportModelOperationsMixin("announcement"), models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
