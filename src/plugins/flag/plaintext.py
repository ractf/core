from plugins.flag.base import FlagPlugin


class PlaintextFlagPlugin(FlagPlugin):
    name = "plaintext"

    def check(self, flag, *args, **kwargs):
        return self.challenge.flag_metadata["flag"] == flag
