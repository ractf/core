import abc
import pickle

from backend import settings
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


class PostgresBackend(ConfigBackend):
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


class RedisBackend(ConfigBackend):

    def __init__(self):
        ip = settings.CONFIG['REDIS']['HOST']
        port = settings.CONFIG['REDIS']['PORT']
        db = settings.CONFIG['REDIS']['DB']
        password = settings.CONFIG['REDIS']['PASSWORD']

        from redis import Redis
        self.redis = Redis(host=ip, port=port, db=db, password=password)

    def get(self, key):
        value = self.redis.get(f'config_{key}')
        if value is None:
            return None
        return pickle.loads(value)

    def set(self, key, value):
        db_config = Config.objects.get(key='config')
        db_config.value[key] = value
        db_config.save()
        self.redis.set(f'config_{key}', pickle.dumps(value))

    def get_all(self):
        config = {}
        for key in self.redis.keys('config_*'):
            config[key[7:].decode('latin-1')] = self.get(key[7:].decode('latin-1'))
        return config

    def set_if_not_exists(self, key, value):
        if not self.redis.exists('config_' + key):
            self.set(key, value)

    def load(self, defaults):
        db_config = Config.objects.filter(key='config')
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
            Config(key='config', value=defaults).save()
            for key, value in defaults.items():
                self.set(key, value)
