import sys
import inspect
from collections import defaultdict
from pydoc import locate

from plugins.flag.base import FlagPlugin
from plugins.points.base import PointsPlugin

plugins = defaultdict(dict)
feature_plugins_by_class = {}


def load_plugins(plugin_list):
    global plugins
    for plugin in plugin_list:
        for name, obj in inspect.getmembers(locate(plugin)):
            if inspect.isclass(obj):
                if obj.__module__ != plugin:
                    continue
                if issubclass(obj, FlagPlugin) or issubclass(obj, PointsPlugin):
                    plugins[obj.plugin_type][obj.name] = obj
                    print(f"Loaded {obj.plugin_type} plugin: {obj.name}({plugin})", file=sys.stderr)
