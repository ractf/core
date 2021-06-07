import binascii
import os
from datetime import timedelta

import pyotp
from django.conf import settings
from django.db import models
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from team.models import Team


class Token(ExportModelOperationsMixin("token"), models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tokens", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_tokens",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        if not self.owner:
            self.owner = self.user
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class InviteCode(ExportModelOperationsMixin("invite_code"), models.Model):
    code = models.CharField(max_length=64, unique=True)
    uses = models.IntegerField(default=0)
    max_uses = models.IntegerField()
    fully_used = models.BooleanField(default=False)
    auto_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)


def one_day():
    return timezone.now() + timedelta(days=1)


class PasswordResetToken(ExportModelOperationsMixin("password_reset_token"), models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    issued = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(default=one_day)


class BackupCode(ExportModelOperationsMixin("backup_code"), models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="backup_codes", on_delete=models.CASCADE)
    code = models.CharField(max_length=8)

    class Meta:
        unique_together = [("user", "code")]

    @staticmethod
    def generate(user):
        BackupCode.objects.filter(user=user).delete()
        codes = [BackupCode(user=user, code=pyotp.random_base32(8)) for i in range(10)]
        BackupCode.objects.bulk_create(codes)
        return BackupCode.objects.filter(user=user).values_list("code", flat=True)


class TOTPDevice(ExportModelOperationsMixin("totp_device"), models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="totp_device",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True)
    totp_secret = models.CharField(null=True, max_length=16, default=pyotp.random_base32)
    verified = models.BooleanField(default=False)

    def validate_token(self, token):
        return pyotp.TOTP(self.totp_secret).verify(token, valid_window=1)
