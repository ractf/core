class IncorrectSolvesMixin:
    def get_incorrect_solves(self, instance):
        """Counts incorrect solves."""
        return instance.solves.filter(correct=False).count()
