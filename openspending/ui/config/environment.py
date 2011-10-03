"""Pylons environment configuration"""
import logging
import os
from gettext import translation

from genshi.template import TemplateLoader
from genshi.filters.i18n import Translator
from pylons import config

from sqlalchemy import engine_from_config

import pylons
from webhelpers import markdown

from openspending.model import init_model
from openspending import mongo

from openspending.plugins import core as plugins
from openspending.plugins.interfaces import IConfigurable, IConfigurer

from openspending.ui.config import routing
from openspending.ui.lib import app_globals
from openspending.ui.lib import helpers


class MultiDomainTranslator(object):
    """ This is used by Genshi to allow using multiple domains within
    a single template. The usage in a plugin would be about the following::

        config['openspending.ui.translations'].add_domain(__name__, locale_dir)

    """
    # TODO: This needs to be reconfigured to enable live language changes.

    def __init__(self, languages):
        self._translations = {}
        self._languages = languages

    def add_domain(self, domain, localedir):
        t = translation(domain, localedir, languages=self._languages)
        self._translations[domain] = t

    def ugettext(self, *a):
        return pylons.translator.ugettext(*a)

    def ungettext(self, *a):
        return pylons.translator.ungettext(*a)

    def dungettext(self, domain, *a):
        if domain in self._translations:
            return self._translations[domain].ungettext(*a)
        return self.ungettext(*a)

    def dugettext(self, domain, *a):
        if domain in self._translations:
            return self._translations[domain].ugettext(*a)
        return self.ugettext(*a)


def load_environment(global_conf, app_conf):
    """\
    Configure the Pylons environment via the ``pylons.config`` object
    """

    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='openspending.ui', paths=paths)

    plugins.load_all(config)

    # Allow plugins implementing IConfigurer to modify the config.
    for plugin in plugins.PluginImplementations(IConfigurer):
        plugin.configure(config)

    config['routes.map'] = routing.make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    config['pylons.h'] = helpers

    # set log level in markdown
    markdown.logger.setLevel(logging.WARN)

    # Translator (i18n)
    config['openspending.ui.translations'] = MultiDomainTranslator([config.get('lang', 'en')])
    translator = Translator(config['openspending.ui.translations'])
    def template_loaded(template):
        translator.setup(template)

    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        search_path=paths['templates'],
        auto_reload=True,
        callback=template_loaded
    )

    # SQLAlchemy
    engine = engine_from_config(config, 'sqlalchemy.')
    init_model(engine)

    # Configure Solr
    import openspending.lib.solr_util as solr
    solr.configure(config)

    # Plugin configuration.
    for plugin in plugins.PluginImplementations(IConfigurable):
        plugin.configure(config)

