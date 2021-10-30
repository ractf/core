from . import *

SECRET_KEY = "CorrectHorseBatteryStaple"

FRONTEND_URL = "http://example.com/"
DOMAIN = "example.com"

EMAIL_BACKEND = "anymail.backends.test.EmailBackend"

for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]:
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = "9999999/minute"

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': 'db.sqlite3',
#        'USER': '',
#        'PASSWORD': '',
#        'HOST': '',
#        'PORT': '',
#    },
# }

# CONFIG = {
#    "BACKEND": "config.backends.DatabaseBackend",
# }

# CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#        'LOCATION': 'dead-beef',
#    }
# }
