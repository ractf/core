import hashlib

from plugins.flag.base import FlagPlugin


class HashedFlagPlugin(FlagPlugin):
    name = "hashed"

    def check(self, flag, *args, **kwargs):
        return self.challenge.flag_metadata["flag"] == hashlib.sha256(flag.encode("utf-8")).hexdigest()

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property of length 64"""
        if len(self.challenge.flag_metadata.get("flag", "")) == 64:
            return ["property 'flag' must be of length 64!"]
        return []
