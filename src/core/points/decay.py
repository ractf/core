"""Decay points plugin."""

from challenges.models import Score
from django.contrib.auth import get_user_model
from django.db.models import F

import team
from core.points.base import PointsPlugin


class DecayPointsPlugin(PointsPlugin):
    """
    Decay points plugin.

    The amount of points decreases exponentially as more users solve the challenge.
    """

    name = "decay"
    recalculate_type = "custom"

    def get_points(self, team, flag, solves, *args, **kwargs):
        """Return the amount of points a solve is worth."""
        challenge = self.challenge
        decay_constant = challenge.challenge_metadata["decay_constant"]
        min_points = challenge.challenge_metadata["min_points"]
        return int(round(min_points + ((challenge.score - min_points) * (decay_constant ** max(solves - 1, 0)))))

    def recalculate(self, teams, users, solves, *args, **kwargs):
        """
        Recalculates the amount of points a solve is worth.

        This will be called on every solve.
        """
        challenge = self.challenge
        points = self.get_points(None, None, solves.count())
        delta = self.get_points(None, None, solves.count() - 1) - points
        scores = Score.objects.filter(solve__in=solves)
        scores.update(points=points)
        team.models.Team.objects.filter(solves__challenge=challenge).update(points=F("points") - delta)
        get_user_model().objects.filter(solves__challenge=challenge).update(points=F("points") - delta)
