from config import config
from plugins.flag.base import FlagPlugin


class PlaintextFlagPlugin(FlagPlugin):
    name = "plaintext"

    def check(self, flag, *args, **kwargs):
        return self.challenge.flag_metadata["flag"] == flag

    def self_check(self):
        if not self.challenge.flag_metadata.get("flag", ""):
            return ["property 'flag' must be set!"]

        set_flag = self.challenge.flag_metadata["flag"]
        if not set_flag.startswith(config.get("flag_prefix")) or not set_flag.endswith("}"):
            return ["flag does not conform to event flag format!"]

        return []
