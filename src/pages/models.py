from django.db import models
from django_prometheus.models import ExportModelOperationsMixin


class Page(ExportModelOperationsMixin("page"), models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    url = models.CharField(max_length=255, unique=True)
