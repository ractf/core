from plugins.points.base import PointsPlugin


class BasicPointsPlugin(PointsPlugin):
    name = "basic"

    def get_points(self, team, flag, solves, *args, **kwargs):
        return self.challenge.score
