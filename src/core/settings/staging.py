"""Settings for running RACTF backend locally."""

# flake8: noqa

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from . import *

sentry_sdk.init(dsn="https://965545cacdd14caca2d2a037af90e7a7@o104250.ingest.sentry.io/5374672", integrations=[DjangoIntegration()], send_default_pii=True)

SEND_MAIL = True

TEMPLATES.insert(
    0,
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
    },
)

MAIL = {
    "SEND_ADDRESS": "no-reply@ractf.co.uk",
    "SEND_NAME": "RACTF",
    "SEND": True,
}

FRONTEND_URL = "https://staging.ractf.co.uk/"
ALLOWED_HOSTS.extend(("staging.ractf.co.uk", "api-elite.ractf.co.uk"))

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "login": "999/second",
    "register": "999/second",
    "2fa": "999/second",
    "password_reset": "999/second",
    "request_password_reset": "999/second",
    "verify_email": "999/second",
    "change_password": "999/second",
    "challenges": "999/second",
    "flag_submit": "999/second",
    "hint": "999/second",
    "use_hint": "999/second",
    "leaderboard": "999/second",
    "self": "999/second",
    "member": "999/second",
    "team": "999/second",
    "team_create": "999/second",
    "team_join": "999/second",
    "config": "999/second",
    "file": "999/second",
    "challenge_instance_get": "999/second",
    "challenge_instance_reset": "999/second",
    "announcement": "999/second",
}
