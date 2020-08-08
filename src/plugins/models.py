from django.conf import settings
from plugins import plugins

plugins.load_plugins(settings.INSTALLED_PLUGINS)
