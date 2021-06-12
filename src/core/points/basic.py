"""Basic points plugin."""

from core.points.base import PointsPlugin


class BasicPointsPlugin(PointsPlugin):
    """Basic points plugin."""

    name = "basic"

    def get_points(self, team, flag, solves, *args, **kwargs):
        """Return the challenge's points value."""
        return self.challenge.score
