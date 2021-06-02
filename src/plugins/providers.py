import abc
from collections import defaultdict

import config

providers = defaultdict(dict)


def register_provider(provider_type, provider):
    providers[provider_type][provider.name] = provider


def get_provider(provider_type):
    return providers[provider_type][config.config.get(provider_type + '_provider')]


class Provider(abc.ABC):
    pass
