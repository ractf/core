import abc


class AchievementPlugin(abc.ABC):
    plugin_type = "achievement"

    def __init__(self, achievement):
        self.achievement = achievement

    @abc.abstractmethod
    def check_completed(self, solve, *args, **kwargs):
        pass

    @abc.abstractmethod
    def check_progress(self, solve, *args, **kwargs):
        pass
