"""Database models for use in authentication."""

import binascii
import os
from typing import Iterable

import pyotp
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from authentication.logic import utils


class Token(ExportModelOperationsMixin("token"), models.Model):
    """A Token used for users to authenticate with RACTF."""

    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey("member.Member", related_name="tokens", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        "member.Member",
        related_name="owned_tokens",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs) -> None:
        """Ensure that self.key and self.user are populated with defaults."""
        self.key = self.key or self.generate_key()
        self.owner = self.owner or self.user
        return super().save(*args, **kwargs)

    def generate_key(self) -> str:
        """Generate an arbitrary random key for use in the token."""
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        """Return this token's key."""
        return self.key


class InviteCode(ExportModelOperationsMixin("invite_code"), models.Model):
    """Invite codes for admins to issue, allowing new users to register."""

    code = models.CharField(max_length=64, unique=True)
    uses = models.IntegerField(default=0)
    max_uses = models.IntegerField()
    fully_used = models.BooleanField(default=False)
    auto_team = models.ForeignKey("team.Team", on_delete=models.CASCADE, null=True)


class PasswordResetToken(ExportModelOperationsMixin("password_reset_token"), models.Model):
    """Auto-expiring tokens used by users to reset their passwords."""

    user = models.ForeignKey("member.Member", on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    issued = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(default=utils.one_day_hence)


class BackupCode(ExportModelOperationsMixin("backup_code"), models.Model):
    """Backup codes for users to authenticate after they have lost a 2FA provider."""

    user = models.ForeignKey("member.Member", related_name="backup_codes", on_delete=models.CASCADE)
    code = models.CharField(max_length=8, default=utils.random_backup_code)

    class Meta:
        """Specify fields which should be used for composite uniqueness."""

        unique_together = [("user", "code")]

    @staticmethod
    def generate_for(user) -> Iterable[str]:
        """Generate backup codes for the given user."""
        backup_codes = [BackupCode(user=user) for _ in range(10)]
        BackupCode.objects.bulk_create(backup_codes)
        return BackupCode.objects.filter(user=user).values_list("code", flat=True)


class TOTPDevice(ExportModelOperationsMixin("totp_device"), models.Model):
    """TOTP Devices used by users as an extra factor of authentication."""

    user = models.OneToOneField(
        "member.Member",
        related_name="totp_device",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True)
    totp_secret = models.CharField(null=True, max_length=16, default=pyotp.random_base32)
    verified = models.BooleanField(default=False)

    def validate_token(self, token: str) -> bool:
        """Validate the provided token using the TOTP secret for this device."""
        return pyotp.TOTP(self.totp_secret).verify(token, valid_window=1)
