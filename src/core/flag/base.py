"""Base class from which all flag plugins inherit."""

import abc

from core.base import Plugin


class FlagPlugin(Plugin, abc.ABC):
    """Base class from which all flag plugins inherit."""

    plugin_type = "flag"

    def __init__(self, challenge):
        """Set the challenge used by this plugin."""
        self.challenge = challenge

    @abc.abstractmethod
    def check(self, flag, *args, **kwargs):
        """Return True if a flag is valid."""
        pass

    @abc.abstractmethod
    def self_check(self):
        """Return a list of strings describing any problems with the configuration of this plugin."""
        pass
