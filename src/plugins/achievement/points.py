from math import floor

from plugins.achievement.base import AchievementPlugin


class MinimumPointsAchievement(AchievementPlugin):
    name = "points"

    def check_completed(self, solve, *args, **kwargs):
        return solve.solved_by.points > self.achievement.metadata["min_points"]

    def check_progress(self, solve, *args, **kwargs):
        return floor((solve.solved_by.points / self.achievement.metadata["min_points"]) * 100) \
            if not self.achievement.metadata["min_points"] <= solve.solved_by.points else 100
