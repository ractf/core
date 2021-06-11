from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField
from django.db import models, transaction
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from challenge.models import Challenge, Solve
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
