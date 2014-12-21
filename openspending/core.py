import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

from openspending import default_settings

logging.basicConfig(level=logging.DEBUG)

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(**config):
    app = Flask(__name__)
    app.config.from_object(default_settings)
    app.config.from_envvar('OPENSPENDING_SETTINGS', silent=True)
    app.config.update(config)
    db.init_app(app)
    login_manager.init_app(app)

    # HACKY SHIT IS HACKY
    from openspending.lib.solr_util import configure as configure_solr
    configure_solr(app.config)

    return app
