"""Pylons environment configuration"""
import logging
import os

from pylons import config

from sqlalchemy import engine_from_config
from migrate.versioning.util import construct_engine

from webhelpers import markdown

from openspending.model import init_model

from openspending.ui.config import routing
from openspending.ui.lib import app_globals
from openspending.ui.lib import helpers


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
    config.init_app(
        global_conf,
        app_conf,
        package='openspending.ui',
        paths=paths)

    config['routes.map'] = routing.make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    config['pylons.h'] = helpers

    # set log level in markdown
    markdown.logger.setLevel(logging.WARN)

    # SQLAlchemy
    engine = engine_from_config(config, 'openspending.db.')
    engine = construct_engine(engine)
    init_model(engine)

    # Configure Solr
    import openspending.lib.solr_util as solr
    solr.configure(config)
