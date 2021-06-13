"""Database models for the member app."""

import secrets
import time
from enum import IntEnum

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CICharField
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from authentication.models import Token, TOTPDevice
from config import config
from core.validators import printable_name


class TOTPStatus(IntEnum):
    """The status of a user's totp device."""

    DISABLED = 0
    VERIFYING = 1
    ENABLED = 2


class Member(ExportModelOperationsMixin("member"), AbstractUser):
    """Represents a member."""

    username_validator = printable_name

    username = CICharField(
        _("username"),
        max_length=36,
        unique=True,
        help_text=_("Required. 36 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[username_validator],
        error_messages={"unique": _("A user with that username already exists.")},
    )
    email = models.EmailField(_("email address"), blank=True, unique=True)
    state_actor = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True, max_length=400)
    discord = models.CharField(blank=True, max_length=36)
    discordid = models.CharField(blank=True, max_length=18)
    twitter = models.CharField(blank=True, max_length=36)
    reddit = models.CharField(blank=True, max_length=36)
    team = models.ForeignKey("team.Team", on_delete=SET_NULL, null=True, related_name="members")
    email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=64, default=secrets.token_hex)
    points = models.IntegerField(default=0)
    leaderboard_points = models.IntegerField(default=0)
    last_score = models.DateTimeField(default=timezone.now)

    totp_device: TOTPDevice

    def __str__(self) -> str:
        """Represent a member as a string, returns the username."""
        return self.username

    @property
    def has_totp_device(self) -> bool:
        """Check if the user has a TOTP device."""
        return hasattr(self, "totp_device") and self.totp_device is not None

    @property
    def can_login(self) -> bool:
        """Check if the user can currently login."""
        return self.is_staff or (
            config.get("enable_login") and (config.get("enable_prelogin") or config.get("start_time") <= time.time())
        )

    def has_2fa(self) -> bool:
        """Check if the user has 2fa enabled."""
        return self.has_totp_device and self.totp_device.verified

    @property
    def should_deny_admin(self) -> bool:
        """Check if the user should be explicitly denied admin perms."""
        return config.get("enable_force_admin_2fa") and not self.has_2fa()

    def issue_token(self, owner=None) -> str:
        """Issue an authentication token for the user."""
        token = Token(user=self, owner=owner)
        token.save()
        return token.key

    def recalculate_score(self) -> None:
        """Recalculate the score for this user and implicity save."""
        self.points = 0
        self.leaderboard_points = 0
        for score in self.scores:
            if score.leaderboard:
                self.leaderboard_points += score.points - score.penalty
            self.points += score.points - score.penalty
        self.save()


class UserIP(ExportModelOperationsMixin("user_ip"), models.Model):
    """Represents the ip and useragent a given user accessed the api from."""

    user = models.ForeignKey("member.Member", on_delete=SET_NULL, null=True)
    ip = models.CharField(max_length=255)
    seen = models.IntegerField(default=1)
    last_seen = models.DateTimeField(default=timezone.now)
    user_agent = models.CharField(max_length=255)

    @staticmethod
    def hook(request):
        """Store the ip and useragent used to make a request in the db."""
        if not request.user.is_authenticated:
            return
        ip = request.headers.get("x-forwarded-for", "0.0.0.0")
        user_agent = request.headers.get("user-agent", "???")
        qs = UserIP.objects.filter(user=request.user, ip=ip)
        if qs.exists():
            user_ip = qs.first()
            user_ip.seen += 1
            user_ip.last_seen = timezone.now()
            user_ip.user_agent = user_agent
            user_ip.save()
        else:
            UserIP(user=request.user, ip=ip, user_agent=user_agent).save()
