from pydoc import locate

from django.conf import settings

backend = locate(settings.CONFIG['BACKEND'])()
backend.load(defaults=settings.DEFAULT_CONFIG)


def get(key):
    return backend.get(key)


def set(key, value):
    backend.set(key, value)


def get_all():
    return backend.get_all()


def get_all_non_sensitive():
    sensitive = backend.get('sensitive_fields')
    config = backend.get_all()
    for field in sensitive:
        del config[field]
    return config


def is_sensitive(key):
    return key in backend.get('sensitive_fields')


def set_bulk(values: dict):
    for key, value in values.items():
        set(key, value)


def add_plugin_config(name, config):
    settings.DEFAULT_CONFIG[name] = config
