import re

from plugins.flag.base import FlagPlugin


class RegexFlagPlugin(FlagPlugin):
    name = 'regex'

    def check(self, flag, *args, **kwargs):
        regex = re.compile(self.challenge.flag_metadata['flag'])
        return regex.fullmatch(flag)
