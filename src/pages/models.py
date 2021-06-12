"""Database models for the pages app."""

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin


class Page(ExportModelOperationsMixin("page"), models.Model):
    """Represents a custom page that will be displayed on the frontend."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    url = models.CharField(max_length=255, unique=True)
