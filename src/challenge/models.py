from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.db.models import SET_NULL, CASCADE, PROTECT, Case, When, Value, UniqueConstraint, Q, Subquery, JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from team.models import Team


class Category(models.Model):
    name = models.CharField(max_length=36, unique=True)
    display_order = models.IntegerField()
    contained_type = models.CharField(max_length=36)
    description = models.TextField()
    metadata = JSONField(default=dict)
    release_time = models.DateTimeField(default=timezone.now)


class Challenge(models.Model):
    name = models.CharField(max_length=36, unique=True)
    category = models.ForeignKey(
        Category, on_delete=PROTECT, related_name="category_challenges"
    )
    description = models.TextField()
    challenge_type = models.CharField(max_length=64)
    challenge_metadata = JSONField()
    post_score_explanation = models.TextField(blank=True)
    flag_type = models.CharField(max_length=64, default="plaintext")
    flag_metadata = JSONField()
    author = models.CharField(max_length=36)
    auto_unlock = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    score = models.IntegerField()
    unlocks = models.ManyToManyField(
        "self", related_name="unlocked_by", blank=True, symmetrical=False
    )
    first_blood = models.ForeignKey(
        get_user_model(),
        related_name="first_bloods",
        on_delete=SET_NULL,
        null=True,
        default=None,
    )
    points_type = models.CharField(max_length=64, default="basic")
    release_time = models.DateTimeField(default=timezone.now)

    def is_unlocked(self, user):
        if not user.is_authenticated:
            return False
        if self.auto_unlock:
            return True
        if user.team is None:
            return False
        solves = user.team.solves.filter(correct=True).values_list("challenge", flat=True)
        if self.unlocked_by.filter(id__in=solves).exists():
            return True
        return False

    def is_solved(self, user):
        if not user.is_authenticated:
            return False
        if user.team is None:
            return False
        return user.team.solves.filter(challenge=self).exists()

    @classmethod
    def get_unlocked_annotated_queryset(cls, user):
        if user.is_staff and user.should_deny_admin():
            return Challenge.objects.none()
        if user.team is not None:
            solved_challenges = Solve.objects.filter(
                team=user.team, correct=True
            ).values_list("challenge")
            challenges = Challenge.objects.annotate(
                unlocked=Case(
                    When(auto_unlock=True, then=Value(True)),
                    When(unlocked_by__in=Subquery(solved_challenges), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                solved=Case(
                    When(id__in=Subquery(solved_challenges), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                unlock_time_surpassed=Case(
                    When(release_time__lte=timezone.now(), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
            )
        else:
            challenges = Challenge.objects.annotate(
                unlocked=Case(
                    When(auto_unlock=True, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                solved=False,
                unlock_time_surpassed=Case(
                    When(release_time__lte=timezone.now(), then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            )
        return challenges


class ChallengeVote(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=CASCADE, related_name="votes")
    user = models.ForeignKey(get_user_model(), on_delete=CASCADE)
    positive = models.BooleanField()


class ChallengeFeedback(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=CASCADE)
    feedback = models.TextField()


@receiver(post_save, sender=Challenge)
def on_challenge_update(sender, instance, created, **kwargs):
    if not created:
        new_score = instance.score


class Score(models.Model):
    team = models.ForeignKey(Team, related_name="scores", on_delete=CASCADE, null=True)
    user = models.ForeignKey(
        get_user_model(), related_name="scores", on_delete=SET_NULL, null=True
    )
    reason = models.CharField(max_length=64)
    points = models.IntegerField()
    penalty = models.IntegerField(default=0)
    leaderboard = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = JSONField(default=dict)


class Solve(models.Model):
    team = models.ForeignKey(Team, related_name="solves", on_delete=CASCADE, null=True)
    challenge = models.ForeignKey(Challenge, related_name="solves", on_delete=CASCADE)
    solved_by = models.ForeignKey(
        get_user_model(), related_name="solves", on_delete=SET_NULL, null=True
    )
    first_blood = models.BooleanField(default=False)
    correct = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    flag = models.TextField()
    score = models.ForeignKey(Score, related_name="solve", on_delete=CASCADE, null=True)

    class Meta:
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
        indexes = [BrinIndex(fields=["challenge"], autosummarize=True)]


def get_file_name(instance, filename):
    return f"{instance.challenge.id}/{instance.md5}/{filename}"


class File(models.Model):
    name = models.CharField(max_length=64)
    url = models.URLField()
    size = models.PositiveBigIntegerField()
    upload = models.FileField(upload_to=get_file_name, null=True)
    challenge = models.ForeignKey(Challenge, on_delete=CASCADE, related_name="file_set")
    md5 = models.CharField(max_length=32, null=True)


class Tag(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=CASCADE)
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    post_competition = models.BooleanField(default=False)
