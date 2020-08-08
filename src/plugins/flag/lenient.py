from config import config
from plugins.flag.base import FlagPlugin
import unicodedata


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def lower(s):
    return s.lower()


def strip_whitespace(s):
    return ''.join(s.split())


def fix_format(s):
    prefix = config.get('flag_prefix')
    return s if prefix + '{' in s else prefix + '{' + s + '}'


passes = {
    'accent_insensitive': strip_accents,
    'case_insensitive': lower,
    'whitespace_insensitive': strip_whitespace,
    'format': fix_format,
}


class LenientFlagPlugin(FlagPlugin):
    name = 'lenient'

    def check(self, flag, *args, **kwargs):
        flag_metadata = self.challenge.flag_metadata
        if 'exclude_passes' not in flag_metadata:
            flag_metadata['exclude_passes'] = []

        real_flag = flag_metadata['flag']
        for operation in passes:
            if operation not in flag_metadata['exclude_passes']:
                flag = passes[operation](flag)
                real_flag = passes[operation](real_flag)
        return real_flag == flag
