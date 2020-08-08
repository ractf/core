import hashlib

from plugins.flag.base import FlagPlugin


class HashedFlagPlugin(FlagPlugin):
    name = "hashed"

    def check(self, flag, *args, **kwargs):
        return self.challenge.flag_metadata["flag"] == hashlib.sha256(flag.encode("utf-8")).hexdigest()
