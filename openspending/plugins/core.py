"""
Provides plugin services to OpenSpending
"""

import logging
from inspect import isclass
from itertools import chain
from pkg_resources import iter_entry_points
from pyutilib.component.core import PluginGlobals, ExtensionPoint as PluginImplementations, implements
from pyutilib.component.core import SingletonPlugin as _pca_SingletonPlugin
from pyutilib.component.core import Plugin as _pca_Plugin
from pyutilib.component.core import PluginEnvironment

__all__ = [
    'PluginImplementations', 'implements',
    'PluginNotFoundException', 'Plugin', 'SingletonPlugin',
    'load', 'load_all', 'unload', 'unload_all',
    'reset'
]

log = logging.getLogger(__name__)

# Entry point group.
PLUGINS_ENTRY_POINT_GROUP = "openspending.plugins"

class PluginNotFoundException(Exception):
    """
    Raised when a requested plugin cannot be found.
    """

class Plugin(_pca_Plugin):
    """
    Base class for plugins which require multiple instances.

    Unless you need multiple instances of your plugin object you should
    probably use SingletonPlugin.
    """

class SingletonPlugin(_pca_SingletonPlugin):
    """
    Base class for plugins which are singletons (ie most of them)

    One singleton instance of this class will be created when the plugin is
    loaded. Subsequent calls to the class constructor will always return the
    same singleton instance.
    """

def _get_service(plugin):
    """
    Return a service (ie an instance of a plugin class).

    :param plugin: any of: the name of a plugin entry point; a plugin class; an
        instantiated plugin object.
    :return: the service object
    """

    if isinstance(plugin, basestring):
        try:
            (plugin,) = iter_entry_points(
                group=PLUGINS_ENTRY_POINT_GROUP,
                name=plugin
            )
        except ValueError:
            raise PluginNotFoundException(plugin)

        return plugin.load()()

    elif isinstance(plugin, _pca_Plugin):
        return plugin

    elif isclass(plugin) and issubclass(plugin, _pca_Plugin):
        return plugin()

    else:
        raise TypeError("Expected a plugin name, class or instance", plugin)


def load_all(config):
    """
    Load all plugins listed in the 'ckan.plugins' config directive.
    """
    plugins = find_plugins(config)
    # PCA default behaviour is to activate SingletonPlugins at import time. We
    # only want to activate those listed in the config, so clear
    # everything then activate only those we want.
    unload_all()

    for plugin in plugins:
        load(plugin)

def reset():
    """
    Clear and reload all configured plugins
    """
    from pylons import config
    load_all(config)

def load(plugin):
    """
    Load a single plugin, given a plugin name, class or instance
    """
    service = _get_service(plugin)
    service.activate()
    return service

def unload_all():
    """
    Unload (deactivate) all loaded plugins
    """
    for env in PluginGlobals.env_registry.values():
        for service in env.services.copy():
            unload(service)

def unload(plugin):
    """
    Unload a single plugin, given a plugin name, class or instance
    """
    service = _get_service(plugin)
    service.deactivate()
    return service

def find_plugins(config):
    """
    Return all plugins specified in the 'openspending.plugins' config directive.
    """
    plugins = []
    for name in config.get('openspending.plugins', '').split():
        entry_points = list(
            iter_entry_points(group=PLUGINS_ENTRY_POINT_GROUP, name=name)
        )
        if not entry_points:
            raise PluginNotFoundException(name)
        plugins.extend(ep.load() for ep in entry_points)
    return plugins
