import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.babel import Babel
from flaskext.gravatar import Gravatar
from flask.ext.cache import Cache
from flaskext.uploads import UploadSet, IMAGES, configure_uploads
import formencode_jinja2

from openspending import default_settings
from openspending.lib.routing import NamespaceRouteRule
from openspending.lib.routing import FormatConverter, NoDotConverter

logging.basicConfig(level=logging.DEBUG)

db = SQLAlchemy()
babel = Babel()
login_manager = LoginManager()
cache = Cache()

badge_images = UploadSet('badgeimages', IMAGES)


def create_app(**config):
    app = Flask(__name__)
    app.url_rule_class = NamespaceRouteRule
    app.url_map.converters['fmt'] = FormatConverter
    app.url_map.converters['nodot'] = NoDotConverter

    app.config.from_object(default_settings)
    app.config.from_envvar('OPENSPENDING_SETTINGS', silent=True)
    app.config.update(config)

    app.jinja_options['extensions'].extend([
        formencode_jinja2.formfill,
        'jinja2.ext.i18n'
    ])

    db.init_app(app)
    babel.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    configure_uploads(app, (badge_images,))

    # HACKY SHIT IS HACKY
    from openspending.lib.solr_util import configure as configure_solr
    configure_solr(app.config)

    from openspending.views import register_views
    register_views(app)

    Gravatar(app, size=200, rating='g',
             default='retro', use_ssl=True)

    return app
