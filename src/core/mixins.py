"""Generic mixins used in RACTF core."""


class IncorrectSolvesMixin:
    """Mixin to add the incorrect_solves attribute to a serializer."""

    def get_incorrect_solves(self, instance):
        """Return the count of incorrect solves."""
        return instance.solves.filter(correct=False).count()
