from . import *

SECRET_KEY = "CorrectHorseBatteryStaple"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

FRONTEND_URL = "http://example.com/"
DOMAIN = "example.com"

for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]:
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = "9999999/minute"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/ractf-linting.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

CONFIG = {
    "BACKEND": "config.backends.CachedBackend",
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/ractf-linting.cache",
        "OPTIONS": {"MAX_ENTRIES": 1000},
        "TIMEOUT": 60,
    },
}
