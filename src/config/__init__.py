from importlib import import_module

from django.utils.functional import SimpleLazyObject


config = SimpleLazyObject(lambda: import_module("config.config", "config"))
