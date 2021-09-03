"""Database models and querysets for the team app."""

import secrets
import time
from enum import IntEnum

from challenges.models import Challenge, Solve
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CICharField
from django.db import models, transaction
from django.db.models import SET_NULL
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from authentication.models import Token, TOTPDevice
from config import config
from core.validators import printable_name


class TeamQuerySet(models.QuerySet):
    """Custom QuerySet for common operations used to filter Teams."""

    def visible(self) -> "models.QuerySet[Team]":
        """Return a QuerySet of teams that are visible."""
        return self.filter(is_visible=True)

    def ranked(self) -> "models.QuerySet[Team]":
        """Return a QuerySet of teams ordered by how they should be displayed."""
        return self.order_by("-leaderboard_points", "last_score")

    def prefetch_solves(self) -> "models.QuerySet[Team]":
        """Prefetch this team's correct solves."""
        return self.prefetch_related(models.Prefetch("solves", queryset=Solve.objects.filter(correct=True)))


class Team(ExportModelOperationsMixin("team"), models.Model):
    """Represents a team of one or more Members."""

    name = CICharField(max_length=36, unique=True, validators=[printable_name])
    is_visible = models.BooleanField(default=True)
    password = models.CharField(max_length=64)
    owner = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="owned_team")
    description = models.TextField(blank=True, max_length=400)
    points = models.IntegerField(default=0)
    leaderboard_points = models.IntegerField(default=0)
    last_score = models.DateTimeField(default=timezone.now)
    size_limit_exempt = models.BooleanField(default=False)

    objects = TeamQuerySet.as_manager()

    @property
    def solved_challenges(self) -> "models.QuerySet[Challenge]":
        """Return the list of challenges the team has solved."""
        return self.solves.filter(correct=True).values_list("challenge", flat=True)

    def recalculate_score(self):
        """Recalculate the score for this team and all its users and implicity save."""
        self.points = 0
        self.leaderboard_points = 0
        for user_unsafe in self.members.all():
            with transaction.atomic():
                user = get_user_model().objects.select_for_update().get(id=user_unsafe.pk)
                user.recalculate_score()
                self.points += user.points
                self.leaderboard_points += user.leaderboard_points
        self.save()


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
        for score in self.scores.all():
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
