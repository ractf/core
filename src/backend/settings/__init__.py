"""Base Django settings for RACTF backend."""

# flake8: noqa

import os
import time
from pathlib import Path

from corsheaders.defaults import default_headers

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
CORS_ALLOW_HEADERS = [*default_headers, "x-exporting", "exporting"]

DOMAIN = os.getenv("DOMAIN")
DEBUG = bool(os.getenv("DEBUG"))
FRONTEND_URL = os.getenv("FRONTEND_URL")
AUTH_USER_MODEL = "member.Member"

BASE_DIR = str(Path(__file__).parent.parent.parent.absolute())
SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]
if DOMAIN:
    ALLOWED_HOSTS.append(DOMAIN)

MAIL = {
    "SEND_ADDRESS": "no-reply@ractf.co.uk",
    "SEND_NAME": "RACTF",
    "SEND": True,
    "SEND_MODE": "SES",
}

EXPERIMENT_OVERRIDES = {}

MAX_UPLOAD_SIZE = 10_000_000_000  # 10gb
USE_AWS_S3_FILE_STORAGE = os.getenv("USE_AWS_S3_FILE_STORAGE")

if USE_AWS_S3_FILE_STORAGE:
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_FILES_BUCKET_NAME")
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_FILES_BUCKET_DOMAIN", AWS_STORAGE_BUCKET_NAME)
    PUBLIC_MEDIA_LOCATION = "challenge-files"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "backend.storages.PublicMediaStorage"
else:
    MEDIA_URL = "/publicmedia/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "publicmedia")

DEFAULT_CONFIG = {
    "config_version": 5,
    "flag_prefix": "ractf",
    "graph_members": 10,
    "register_start_time": time.time(),
    "register_end_time": -1,
    "end_time": time.time() + 7 * 24 * 60 * 60,
    "start_time": time.time(),
    "team_size": -1,
    "email_allow": "a",
    "login_provider": "basic_auth",
    "registration_provider": "basic_auth",
    "token_provider": "basic_auth",
    "enable_bot_users": True,
    "enable_caching": True,
    "enable_challenge_server": True,
    "enable_ctftime": True,
    "enable_flag_submission": True,
    "enable_flag_submission_after_competition": True,
    "enable_force_admin_2fa": False,
    "enable_track_incorrect_submissions": True,
    "enable_login": True,
    "enable_prelogin": True,
    "enable_maintenance_mode": False,
    "enable_registration": True,
    "enable_preevent_cache": True,
    "enable_scoreboard": True,
    "enable_scoring": True,
    "enable_solve_broadcast": True,
    "enable_teams": True,
    "enable_team_join": True,
    "enable_view_challenges_after_competion": True,
    "enable_team_leave": False,
    "invite_required": False,
    "hide_scoreboard_at": -1,
    "setup_wizard_complete": False,
    "sensitive_fields": ["sensitive_fields", "enable_force_admin_2fa", "firstblood_webhook"],
    "firstblood_webhook": "",
    "event_name": "RACTF",
}

INSTALLED_APPS = [
    "admin.apps.AdminConfig",
    "announcements.apps.AnnouncementsConfig",
    "authentication.apps.AuthConfig",
    "challenge.apps.ChallengeConfig",
    "andromeda.apps.AndromedaConfig",
    "config.apps.ConfigConfig",
    "experiments.apps.ExperimentsConfig",
    "hint.apps.HintConfig",
    "leaderboard.apps.LeaderboardConfig",
    "member.apps.MemberConfig",
    "pages.apps.PagesConfig",
    "plugins.apps.PluginsConfig",
    "ractf.apps.RactfConfig",
    "scorerecalculator.apps.ScorerecalculatorConfig",
    "team.apps.TeamConfig",
    "sockets.apps.SocketsConfig",
    "stats.apps.StatsConfig",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.psutil",
    "health_check.contrib.redis",
    "rest_framework",
    "rest_framework.authtoken",
    "django_zxcvbn_password_validator",
    "channels",
    "storages",
    "corsheaders",
    "cachalot",
    "django_prometheus",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "clacks.middleware.ClacksMiddleware",
    "querycount.middleware.QueryCountMiddleware",
]
if DEBUG:
    MIDDLEWARE.insert(0, "better_exceptions.integrations.django.BetterExceptionsMiddleware")

if os.getenv("ENABLE_SILK"):
    INSTALLED_APPS.insert(len(INSTALLED_APPS) - 6, "silk")
    MIDDLEWARE.insert(len(MIDDLEWARE) - 2, "silk.middleware.SilkyMiddleware")
    SILKY_PYTHON_PROFILER = True


ROOT_URLCONF = "backend.urls"

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, "templates"),
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "sockets.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(os.getenv("REDIS_HOST"), os.getenv("REDIS_PORT"))]},
    },
}


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "PASSWORD": os.getenv("SQL_PASSWORD"),
        "NAME": os.getenv("SQL_DATABASE"),
        "USER": os.getenv("SQL_USER"),
        "HOST": os.getenv("SQL_HOST"),
        "PORT": os.getenv("SQL_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "django_zxcvbn_password_validator.ZxcvbnPasswordValidator"},
]


PASSWORD_MINIMAL_STRENGTH = 3


AUTHENTICATION_BACKENDS = ["backend.backends.EmailOrUsernameBackend"]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/api/v2/static/"
STATIC_ROOT = "/srv/django_static"

RATELIMIT_ENABLE = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "backend.renderers.RACTFJSONRenderer",
        "rest_framework.renderers.JSONRenderer",
    ),
    "EXCEPTION_HANDLER": "backend.exception_handler.handle_exception",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.authentication.RactfTokenAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": ["backend.throttling.AdminBypassThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/minute",
        "register": "10/minute",
        "2fa": "1000/day",
        "password_reset": "3/minute",
        "request_password_reset": "5/hour",
        "resend_verify_email": "5/hour",
        "verify_email": "3/minute",
        "change_password": "10/minute",
        "challenges": "99999/minute",
        "flag_submit": "10/minute",
        "hint": "5/minute",
        "use_hint": "3/minute",
        "leaderboard": "5/minute",
        "self": "30/minute",
        "member": "100/minute",
        "team": "100/minute",
        "team_create": "30/hour",
        "team_join": "20/minute",
        "config": "100/minute",
        "file": "100/minute",
        "challenge_instance_get": "20/minute",
        "challenge_instance_reset": "10/hour",
        "announcement": "100/minute",
        "tag": "100/minute",
        "pages": "100/minute",
        "andromeda_view_jobs": "100/minute",
        "andromeda_manage_jobs": "100/minute",
        "andromeda_view_sysinfo": "100/minute",
        "polaris_view_challenges": "100/minute",
        "polaris_submit_challenge": "100/minute",
        "polaris_delete_challenge": "100/minute",
        "polaris_view_deployments": "100/minute",
        "polaris_submit_deployments": "10/minute",
        "polaris_delete_deployments": "100/minute",
        "polaris_view_hosts": "100/minute",
        "polaris_view_instances": "100/minute",
    },
    "DEFAULT_PAGINATION_CLASS": "backend.pagination.FormattedPagination",
    "PAGE_SIZE": 100,
    "NUM_PROXIES": int(os.getenv("NUM_PROXIES", 0)),
}

MAIL_SOCK_URL = "http+unix://%2Ftmp%2Fmailusv.sock/send"
SEND_MAIL = False

if os.getenv("CHALLENGE_SERVER_TYPE") == "POLARIS":
    POLARIS_URL = os.getenv("POLARIS_URL")
    POLARIS_USERNAME = os.getenv("POLARIS_USERNAME")
    POLARIS_PASSWORD = os.getenv("POLARIS_PASSWORD")
else:
    ANDROMEDA_URL = os.getenv("ANDROMEDA_URL")
    ANDROMEDA_API_KEY = os.getenv("ANDROMEDA_API_KEY")
    ANDROMEDA_SERVER_IP = os.getenv("ANDROMEDA_IP")  # shown to participants

INSTALLED_PLUGINS = [
    "plugins.flag.hashed",
    "plugins.flag.plaintext",
    "plugins.flag.regex",
    "plugins.flag.lenient",
    "plugins.flag.long_text",
    "plugins.flag.map",
    "plugins.points.basic",
    "plugins.points.decay",
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
        "OPTIONS": {
            "DB": int(os.getenv("REDIS_CACHE_DB", 0)),
            "PASSWORD": None,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {"max_connections": 50, "timeout": 20},
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    }
}
REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

CONFIG = {
    "BACKEND": "config.backends.CachedBackend",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s %(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "propagate": False,
            "level": "DEBUG",
        },
        "core.handlers": {"level": "DEBUG", "handlers": ["console"]},
    },
}

REQUIRED_SETTINGS = ["FRONTEND_URL", "DOMAIN"]
