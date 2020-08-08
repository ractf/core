import abc


class FlagPlugin(abc.ABC):
    plugin_type = "flag"

    def __init__(self, challenge):
        self.challenge = challenge

    @abc.abstractmethod
    def check(self, flag, *args, **kwargs):
        pass
