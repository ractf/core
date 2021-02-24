from . import *


SECRET_KEY = "CorrectHorseBatteryStaple"

MAIL["SEND"] = False

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': 'db.sqlite3',
#        'USER': '',
#        'PASSWORD': '',
#        'HOST': '',
#        'PORT': '',
#    },
#}

CONFIG = {
    "BACKEND": "config.backends.DatabaseBackend",
}

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#        'LOCATION': 'dead-beef',
#    }
#}
