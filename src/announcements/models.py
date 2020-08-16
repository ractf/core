from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        permissions = [
            ('add_announcement', 'add_announcement'),
            ('change_announcement', 'change_announcement'),
            ('delete_announcement', 'delete_announcement'),
        ]
