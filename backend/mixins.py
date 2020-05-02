class IncorrectSolvesMixin:

    def get_incorrect_solves(self, instance):
        return instance.solves.filter(correct=False).count()
