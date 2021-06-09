from django.contrib.auth import get_user_model
from django.db.models import F

import team
from challenge.models import Score
from plugins.points.base import PointsPlugin


class DecayPointsPlugin(PointsPlugin):
    name = "decay"
    recalculate_type = "custom"

    def get_points(self, team, flag, solves, *args, **kwargs):
        challenge = self.challenge
        decay_constant = challenge.challenge_metadata["decay_constant"]
        min_points = challenge.challenge_metadata["min_points"]
        return int(round(min_points + ((challenge.score - min_points) * (decay_constant ** max(solves - 1, 0)))))

    def recalculate(self, teams, users, solves, *args, **kwargs):
        challenge = self.challenge
        points = self.get_points(None, None, solves.count())
        delta = self.get_points(None, None, solves.count() - 1) - points
        scores = Score.objects.filter(solve__in=solves)
        scores.update(points=points)
        team.models.Team.objects.filter(solves__challenge=challenge).update(points=F("points") - delta)
        get_user_model().objects.filter(solves__challenge=challenge).update(points=F("points") - delta)
