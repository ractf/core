from django.db import models


class Page(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    url = models.CharField(max_length=255)
