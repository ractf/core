"""Plaintext flag plugin."""

from config import config
from core.flag.base import FlagPlugin


class PlaintextFlagPlugin(FlagPlugin):
    """Plaintext flag plugin."""

    name = "plaintext"

    def check(self, flag, *args, **kwargs):
        """Return True if the flag matches the stored plaintext."""
        return self.challenge.flag_metadata["flag"] == flag

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property and the flag matches the format."""
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]

        set_flag = self.challenge.flag_metadata["flag"]
        if not set_flag.startswith(config.get("flag_prefix")):
            return ["flag does not conform to event flag format!"]

        return []
