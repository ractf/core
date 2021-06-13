"""Flag plugin for leniently validating flags."""

import unicodedata

from config import config
from core.flag.base import FlagPlugin


def strip_accents(s):
    """Remove the accents from characters in a flag."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def lower(s):
    """Make the flag lowercase."""
    return s.lower()


def strip_whitespace(s):
    """Strip all whitespace from a flag."""
    return "".join(s.split())


def fix_format(s):
    """Correct the flag format."""
    prefix = config.get("flag_prefix")
    return s if prefix + "{" in s else prefix + "{" + s + "}"


passes = {
    "accent_insensitive": strip_accents,
    "case_insensitive": lower,
    "whitespace_insensitive": strip_whitespace,
    "format": fix_format,
}


class LenientFlagPlugin(FlagPlugin):
    """Flag plugin for leniently validating flags."""

    name = "lenient"

    def check(self, flag, *args, **kwargs):
        """Return True if the flag is valid after cleaning."""
        flag_metadata = self.challenge.flag_metadata
        if "exclude_passes" not in flag_metadata:
            flag_metadata["exclude_passes"] = []

        real_flag = flag_metadata["flag"]
        for operation in passes:
            if operation not in flag_metadata["exclude_passes"]:
                flag = passes[operation](flag)
                real_flag = passes[operation](real_flag)
        return real_flag == flag

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property."""
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]
        return []
