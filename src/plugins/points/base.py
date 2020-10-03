import abc
import time

from django.db.models import Sum, F
from django.utils import timezone

from challenge.models import Score, Solve, HintUse
from config import config


class PointsPlugin(abc.ABC):
    plugin_type = 'points'
    recalculate_type = 'none'

    def __init__(self, challenge):
        self.challenge = challenge

    @abc.abstractmethod
    def get_points(self, team, flag, solves, *args, **kwargs):
        pass

    def recalculate(self, teams, users, solves, *args, **kwargs):
        pass

    def score(self, user, team, flag, solves, *args, **kwargs):
        challenge = self.challenge
        points = self.get_points(team, flag, solves.count())
        if team is not None:
            deducted = HintUse.objects.filter(team=team, challenge=challenge).aggregate(points=Sum(F('hint__penalty')))
        else:
            deducted = HintUse.objects.filter(user=user, challenge=challenge).aggregate(points=Sum(F('hint__penalty')))
        deducted = 0 if deducted['points'] is None else deducted['points']
        deducted = min(points, deducted)
        scored = config.get('end_time') >= time.time() and config.get('enable_scoring')
        score = Score(team=team, reason='challenge', points=points, penalty=deducted, leaderboard=scored, user=user)
        score.save()
        solve = Solve(team=team, solved_by=user, challenge=challenge, first_blood=challenge.first_blood is None,
                      flag=flag, score=score)
        solve.save()
        user.points += (points - deducted)
        if team is not None:
            team.points += (points - deducted)
        if scored:
            user.leaderboard_points += (points - deducted)
            if team is not None:
                team.leaderboard_points += (points - deducted)
            user.last_score = timezone.now()
            team.last_score = timezone.now()
        return solve

    def register_incorrect_attempt(self, user, team, flag, solves, *args, **kwargs):
        if config.get('enable_track_incorrect_submissions'):
            Solve(team=team, solved_by=user, challenge=self.challenge, flag=flag, correct=False, score=None).save()
