from datetime import timedelta

import pyotp
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from team.models import Team


class InviteCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    uses = models.IntegerField(default=0)
    max_uses = models.IntegerField()
    fully_used = models.BooleanField(default=False)
    auto_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)


def one_day():
    return timezone.now() + timedelta(days=1)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    issued = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(default=one_day)


class BackupCode(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='backup_codes', on_delete=models.CASCADE)
    code = models.CharField(max_length=8)

    class Meta:
        unique_together = [
            ('user', 'code')
        ]

    @staticmethod
    def generate(user):
        BackupCode.objects.filter(user=user).delete()
        codes = [BackupCode(user=user, code=pyotp.random_base32(8)) for i in range(10)]
        BackupCode.objects.bulk_create(codes)
        return BackupCode.objects.filter(user=user).values_list('code', flat=True)


class TOTPDevice(models.Model):
    user = models.OneToOneField(get_user_model(), related_name='totp_device', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True)
    totp_secret = models.CharField(null=True, max_length=16, default=pyotp.random_base32)
    verified = models.BooleanField(default=False)

    def validate_token(self, token):
        return pyotp.TOTP(self.totp_secret).verify(token, valid_window=1)
