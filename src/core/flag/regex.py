import re

from core.flag.base import FlagPlugin


class RegexFlagPlugin(FlagPlugin):
    name = "regex"

    def check(self, flag, *args, **kwargs):
        regex = re.compile(self.challenge.flag_metadata["flag"])
        return regex.fullmatch(flag)

    def self_check(self):
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]
        return []
