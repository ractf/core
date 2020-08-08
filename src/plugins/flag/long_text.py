import string

from plugins.flag.base import FlagPlugin

WHITELIST = string.ascii_lowercase + string.ascii_uppercase


def clean(text):
    return "".join(i for i in text if i in WHITELIST).lower()


class LongTextFlagPlugin(FlagPlugin):
    name = "long_text"

    def check(self, flag, *args, **kwargs):
        return clean(self.challenge.flag_metadata["flag"]) == clean(flag)
