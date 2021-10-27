"""Settings for running RACTF backend locally."""

# flake8: noqa

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from . import *

SEND_MAIL = True

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

TEMPLATES.insert(
    0,
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
    },
)

MAIL = {
    "SEND_ADDRESS": os.getenv("EMAIL_ADDRESS"),
    "SEND_NAME": os.getenv("EMAIL_NAME"),
    "SEND": True,
    "SEND_MODE": os.getenv("EMAIL_PROVIDER"),
    "SEND_SERVER": os.getenv("EMAIL_SERVER"),
    "SEND_USERNAME": os.getenv("EMAIL_USER"),
    "SEND_PASSWORD": os.getenv("EMAIL_PASS"),
    "SMTP_USE_SSL": os.getenv("EMAIL_SSL"),
    "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY"),
}

DEFAULT_SENTRY_DSN = "https://1fb04d3b9f8b4343bccea1c9f5b6d08b@o104250.ingest.sentry.io/5374671"

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", DEFAULT_SENTRY_DSN),
    integrations=[DjangoIntegration(), RedisIntegration()],
    send_default_pii=False,
    server_name=DOMAIN,
)

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "challenges": "4/second",
        "leaderboard": "4/second",
        "self": "4/second",
        "member": "4/second",
        "team": "4/second",
        "config": "4/second",
        "announcement": "4/second",
    }
)
