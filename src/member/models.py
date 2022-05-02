import secrets
import time
from enum import IntEnum

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import SET_NULL
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from backend.validators import printable_name
from config import config


class TOTPStatus(IntEnum):
    DISABLED = 0
    VERIFYING = 1
    ENABLED = 2


class Member(ExportModelOperationsMixin("member"), AbstractUser):
    username_validator = printable_name

    username = models.CharField(
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('username'),
                name='member_member_username_uniq_idx',
            ),
        ]

    def __str__(self):
        return self.username

    def can_login(self):
        return self.is_staff or (
            config.get("enable_login") and (config.get("enable_prelogin") or config.get("start_time") <= time.time())
        )

    def issue_token(self, owner=None):
        from authentication.models import Token

        token = Token(user=self, owner=owner)
        token.save()
        return token.key

    def has_2fa(self):
        return hasattr(self, "totp_device") and self.totp_device.verified

    def should_deny_admin(self):
        return config.get("enable_force_admin_2fa") and not self.has_2fa()


class UserIP(ExportModelOperationsMixin("user_ip"), models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=SET_NULL, null=True, related_name="ips")
    ip = models.GenericIPAddressField()
    seen = models.IntegerField(default=1)
    last_seen = models.DateTimeField(default=timezone.now)
    user_agent = models.CharField(max_length=255)

    @staticmethod
    def hook(request):
        if not request.user.is_authenticated:
            return
        ip = request.headers.get("x-forwarded-for", request.META.get("REMOTE_ADDR", "0.0.0.0")).split(",")[0]
        user_agent = request.headers.get("user-agent", "???")[:255]
        qs = UserIP.objects.filter(user=request.user, ip=ip)
        if qs.exists():
            user_ip = qs.first()
            user_ip.seen += 1
            user_ip.last_seen = timezone.now()
            user_ip.user_agent = user_agent
            user_ip.save()
        else:
            UserIP(user=request.user, ip=ip, user_agent=user_agent).save()
