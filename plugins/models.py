from backend import settings
from plugins import plugins

plugins.load_plugins(settings.INSTALLED_PLUGINS)
