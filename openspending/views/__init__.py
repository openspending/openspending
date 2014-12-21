from flask import current_app

from openspending.views.home import blueprint as home


def register_views(app):
    app.register_blueprint(home)


