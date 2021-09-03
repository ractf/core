"""Database models used by the challenge app."""

import time
from typing import Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.db.models import (
    CASCADE,
    PROTECT,
    SET_NULL,
    Case,
    JSONField,
    Q,
    UniqueConstraint,
    Value,
    When,
)
from django.db.models.aggregates import Count
from django.db.models.query import Prefetch
from django.utils import timezone
from django.utils.functional import cached_property
from django_prometheus.models import ExportModelOperationsMixin

from challenges.logic import evaluate_rpn, get_file_path
from config import config
from core import plugins

USING_POSTGRES = settings.DATABASES.get("default", {}).get("ENGINE", "").endswith("postgresql")


class Category(ExportModelOperationsMixin("category"), models.Model):
    """Represents a category containing 0 or more challenges."""

    name = models.CharField(max_length=36, unique=True)
    display_order = models.IntegerField()
    contained_type = models.CharField(max_length=36)
    description = models.TextField()
    metadata = JSONField(default=dict)
    release_time = models.DateTimeField(default=timezone.now)


class Challenge(ExportModelOperationsMixin("challenge"), models.Model):
    """Represents a challenge object."""

    name = models.CharField(max_length=36, unique=True)
    category = models.ForeignKey("challenge.Category", on_delete=PROTECT, related_name="category_challenges")
    description = models.TextField()
    challenge_type = models.CharField(max_length=64)
    challenge_metadata = JSONField()
    post_score_explanation = models.TextField(blank=True)
    flag_type = models.CharField(max_length=64, default="plaintext")
    flag_metadata = JSONField()
    author = models.CharField(max_length=36)
    hidden = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    score = models.IntegerField()
    unlock_requirements = models.CharField(max_length=255, null=True, blank=True)
    first_blood = models.ForeignKey(
        "teams.Member",
        related_name="first_bloods",
        on_delete=SET_NULL,
        null=True,
        default=None,
    )
    points_type = models.CharField(max_length=64, default="basic")
    release_time = models.DateTimeField(default=timezone.now)
    tiebreaker = models.BooleanField(default=True, help_text="Should the challenge be able to break ties?")

    def self_check(self):
        """Check the challenge doesn't have any configuration issues."""
        issues = []

        if not self.score:
            issues.append({"issue": "missing_points", "challenge": self.pk})

        if not self.flag_type:
            issues.append({"issue": "missing_flag_type", "challenge": self.pk})
        elif type(self.flag_metadata) != dict:
            issues.append({"issue": "invalid_flag_data_type", "challenge": self.pk})
        else:
            issues += [
                {"issue": "invalid_flag_data", "extra": issue, "challenge": self.pk}
                for issue in self.flag_plugin.self_check()
            ]

        return issues

    @cached_property
    def flag_plugin(self):
        """Return the flag plugin responsible for validating flags sent to this challenge."""
        return plugins.plugins["flag"][self.flag_type](self)

    @cached_property
    def points_plugin(self):
        """Return the points plugin responsible for granting points from this challenge."""
        return plugins.plugins["points"][self.points_type](self)

    def is_unlocked_by(self, user: Union["teams.models.Member", AnonymousUser, None], solves=None) -> bool:
        """Check if the provided user has unlocked this challenge."""
        if user is None or not user.is_authenticated or not user.team:
            return False
        return evaluate_rpn(self.unlock_requirements, solves or user.team.solved_challenges)

    def is_solved_by(self, user, solves=None) -> bool:
        """Return True if the provided user has solved this challenge."""
        if not user.is_authenticated or user.team is None:
            return False
        solves = solves or user.team.solved_challenges
        return self.pk in solves

    def get_solve_count(self, solve_counter):
        """Return the solve count of this challenge."""
        return solve_counter.get(self.pk, 0)

    @classmethod
    def get_unlocked_annotated_queryset(cls, user):
        """Get a queryset of all challenges, annotated with if they're unlocked and solved."""
        if user.is_staff and user.should_deny_admin:
            return Challenge.objects.none()
        if user.team is not None:
            challenges = Challenge.objects.annotate(
                solve_count=Count("solves", filter=Q(solves__correct=True)),
                unlock_time_surpassed=Case(
                    When(release_time__lte=timezone.now(), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
            )
        else:
            challenges = Challenge.objects.annotate(
                solved=Value(False, models.BooleanField()),
                solve_count=Count("solves", distinct=True),
                unlock_time_surpassed=Case(
                    When(release_time__lte=timezone.now(), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
            )
        from hint.models import Hint, HintUse

        x = challenges.prefetch_related(
            Prefetch(
                "hint_set",
                queryset=Hint.objects.annotate(
                    used=Case(
                        When(
                            id__in=HintUse.objects.filter(team=user.team).values_list("hint_id"),
                            then=Value(True),
                        ),
                        default=Value(False),
                        output_field=models.BooleanField(),
                    )
                ),
                to_attr="hints",
            ),
            Prefetch("file_set", queryset=File.objects.all(), to_attr="files"),
            Prefetch(
                "tag_set",
                queryset=Tag.objects.all()
                if time.time() > config.get("end_time")
                else Tag.objects.filter(post_competition=False),
                to_attr="tags",
            ),
            "first_blood",
            "hint_set__uses",
        )
        return x


class ChallengeVote(ExportModelOperationsMixin("challenge_vote"), models.Model):
    """Represents a user's vote on a Challenge."""

    challenge = models.ForeignKey("challenge.Challenge", on_delete=CASCADE, related_name="votes")
    user = models.ForeignKey("teams.Member", on_delete=CASCADE)
    positive = models.BooleanField()


class ChallengeFeedback(ExportModelOperationsMixin("challenge_feedback"), models.Model):
    """Represents a user's feedback on a Challenge."""

    challenge = models.ForeignKey("challenge.Challenge", on_delete=CASCADE)
    user = models.ForeignKey("teams.Member", on_delete=CASCADE)
    feedback = models.TextField()


class Score(ExportModelOperationsMixin("score"), models.Model):
    """Represents a score contributing to a team and/or user's points."""

    team = models.ForeignKey("team.Team", related_name="scores", on_delete=CASCADE, null=True)
    user = models.ForeignKey("teams.Member", related_name="scores", on_delete=SET_NULL, null=True)
    reason = models.CharField(max_length=64)
    points = models.IntegerField()
    penalty = models.IntegerField(default=0)
    leaderboard = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = JSONField(default=dict)
    tiebreaker = models.BooleanField(default=True, help_text="Should the score be able to break ties?")


class Solve(ExportModelOperationsMixin("solve"), models.Model):
    """Represents a user and team's solve of a challenge."""

    team = models.ForeignKey("team.Team", related_name="solves", on_delete=CASCADE, null=True)
    challenge = models.ForeignKey("challenge.Challenge", related_name="solves", on_delete=CASCADE)
    solved_by = models.ForeignKey("teams.Member", related_name="solves", on_delete=SET_NULL, null=True)
    first_blood = models.BooleanField(default=False)
    correct = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    flag = models.TextField()
    score = models.ForeignKey("challenge.Score", related_name="solve", on_delete=CASCADE, null=True)

    class Meta:
        """The constraints and indexes on the model."""

        constraints = [
            UniqueConstraint(
                fields=["team", "challenge"],
                condition=Q(correct=True, team__isnull=False),
                name="unique_team_challenge_correct",
            ),
            UniqueConstraint(
                fields=["solved_by", "challenge"],
                condition=Q(correct=True),
                name="unique_member_challenge_correct",
            ),
        ]
        indexes = [BrinIndex(fields=["challenge"], autosummarize=True)] if USING_POSTGRES else []


class File(ExportModelOperationsMixin("file"), models.Model):
    """Represents a file attached to a challenge."""

    name = models.CharField(max_length=64)
    url = models.URLField()
    size = models.PositiveBigIntegerField()
    upload = models.FileField(upload_to=get_file_path, null=True)
    challenge = models.ForeignKey("challenge.Challenge", on_delete=CASCADE, related_name="file_set")
    md5 = models.CharField(max_length=32, null=True)


class Tag(ExportModelOperationsMixin("tag"), models.Model):
    """Represents a tag on a challenge."""

    challenge = models.ForeignKey("challenge.Challenge", on_delete=CASCADE)
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    post_competition = models.BooleanField(default=False)
