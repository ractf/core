import abc
import sys
import pickle
from unittest.mock import MagicMock

from django.core.cache import caches
from config.models import Config


class ConfigBackend(abc.ABC):
    @abc.abstractmethod
    def get(self, key):
        pass

    @abc.abstractmethod
    def set(self, key, value):
        pass

    @abc.abstractmethod
    def get_all(self):
        pass

    def load(self, defaults):
        pass

    def save(self):
        pass


class DatabaseBackend(ConfigBackend):
    """Only use this if you absolutely have to"""

    def get(self, key):
        value = Config.objects.get(key=key).value['value']
        return value

    def set(self, key, value):
        setting = Config.objects.get(key=key)
        setting.value['value'] = value
        setting.save()

    def get_all(self):
        config = {}
        for item in Config.objects.all():
            config[item.key] = item.value['value']
        return config


class CachedBackend(ConfigBackend):

    CONFIG_SET = Config.objects if "migrate" not in sys.argv else MagicMock()

    def __init__(self):
        self.cache = caches["default"]
        self.keys = set()

    def get(self, key):
        value = self.cache.get(f'config_{key}')
        if value is None:
            return None
        return pickle.loads(value)

    def set(self, key, value):
        if type(self.CONFIG_SET) is MagicMock:
            return
        db_config = self.CONFIG_SET.filter(key='config').first()
        if db_config:
            db_config.value[key] = value
            db_config.save()
        self.cache.set(f'config_{key}', pickle.dumps(value), timeout=None)
        self.keys.add(f"config_{key}")

    def get_all(self):
        config = {}
        for key in self.keys:
            config[key[7:]] = self.get(key[7:])
        return config

    def set_if_not_exists(self, key, value):
        if self.cache.add('config_' + key, pickle.dumps(value), timeout=None):
            self.keys.add(f"config_{key}")

    def load(self, defaults):
        if type(self.CONFIG_SET) is MagicMock:
            return
        db_config = self.CONFIG_SET.filter(key='config')
        if db_config.exists():
            config = db_config[0].value
            if 'config_version' not in config or config['config_version'] < defaults['config_version']:
                for key, value in defaults.items():
                    self.set(key, value)
                return
            for key, value in defaults.items():
                self.set_if_not_exists(key, value)
            for key, value in config.items():
                self.set(key, value)
        else:
            Config.objects.create(key='config', value=defaults)
            for key, value in defaults.items():
                self.set(key, value)
