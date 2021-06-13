"""Flag plugin for validating sha256 hashed flags."""

import hashlib

from core.flag.base import FlagPlugin


class HashedFlagPlugin(FlagPlugin):
    """Flag plugin for validating sha256 hashed flags."""

    name = "hashed"

    def check(self, flag, *args, **kwargs):
        """Return True if the hash of the input matches the stored sha256."""
        return self.challenge.flag_metadata["flag"] == hashlib.sha256(flag.encode("utf-8")).hexdigest()

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property of length 64."""
        if len(self.challenge.flag_metadata.get("flag", "")) == 64:
            return ["property 'flag' must be of length 64!"]
        return []
