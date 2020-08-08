import secrets
import time
from enum import IntEnum

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import CICharField
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token

from backend.validators import printable_name
from config import config


class TOTPStatus(IntEnum):
    DISABLED = 0
    VERIFYING = 1
    ENABLED = 2


class Member(AbstractUser):
    username_validator = printable_name

    username = CICharField(
        _("username"),
        max_length=36,
        unique=True,
        help_text=_(
            "Required. 36 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={"unique": _("A user with that username already exists."),},
    )
    email = models.EmailField(_("email address"), blank=True, unique=True)
    totp_secret = models.CharField(null=True, max_length=16)
    totp_status = models.IntegerField(
        choices=[(status, status.value) for status in TOTPStatus],
        default=TOTPStatus.DISABLED,
    )
    is_visible = models.BooleanField(default=False)
    bio = models.TextField(blank=True, max_length=400)
    discord = models.CharField(blank=True, max_length=36)
    discordid = models.CharField(blank=True, max_length=18)
    twitter = models.CharField(blank=True, max_length=36)
    reddit = models.CharField(blank=True, max_length=36)
    team = models.ForeignKey(
        "team.Team", on_delete=SET_NULL, null=True, related_name="members"
    )
    email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=64, default=secrets.token_hex)
    password_reset_token = models.CharField(max_length=64, default=secrets.token_hex)
    points = models.IntegerField(default=0)
    leaderboard_points = models.IntegerField(default=0)
    last_score = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

    def can_login(self):
        return (
            self.is_staff
            or config.get("enable_prelogin")
            or (config.get("enable_login") and config.get("start_time") <= time.time())
        )

    def issue_token(self):
        token, created = Token.objects.get_or_create(user=self)
        return token.key

    def is_2fa_enabled(self):
        return self.totp_status == TOTPStatus.ENABLED

    def should_deny_admin(self):
        return self.totp_status != TOTPStatus.ENABLED and config.get(
            "enable_force_admin_2fa"
        )


class UserIP(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=SET_NULL, null=True)
    ip = models.CharField(max_length=255)
    seen = models.IntegerField(default=1)
    last_seen = models.DateTimeField(default=timezone.now)
    user_agent = models.CharField(max_length=255)

    @staticmethod
    def hook(request):
        if not request.user.is_authenticated:
            return
        ip = request.headers.get('x-forwarded-for')
        user_agent = request.headers.get('user-agent')
        qs = UserIP.objects.filter(user=request.user, ip=ip)
        if qs.exists():
            user_ip = qs.first()
            user_ip.seen += 1
            user_ip.last_seen = timezone.now()
            user_ip.user_agent = user_agent
            user_ip.save()
        else:
            UserIP(user=request.user, ip=ip, user_agent=user_agent).save()
