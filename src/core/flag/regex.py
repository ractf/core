"""Regex based flag validation plugin."""

import re

from core.flag.base import FlagPlugin


class RegexFlagPlugin(FlagPlugin):
    """Plugin to validate flags with regex."""

    name = "regex"

    def check(self, flag, *args, **kwargs):
        """Return True if the entire flag matches a regex."""
        regex = re.compile(self.challenge.flag_metadata["flag"])
        return regex.fullmatch(flag)

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property."""
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]
        return []
