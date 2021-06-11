import string

from core.flag.base import FlagPlugin

WHITELIST = string.ascii_lowercase + string.ascii_uppercase


def clean(text):
    return "".join(i for i in text if i in WHITELIST).lower()


class LongTextFlagPlugin(FlagPlugin):
    name = "long_text"

    def check(self, flag, *args, **kwargs):
        return clean(self.challenge.flag_metadata["flag"]) == clean(flag)

    def self_check(self):
        """Ensure the set flag metadata has a 'flag' property"""
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]
        return []
