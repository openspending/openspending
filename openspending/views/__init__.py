from openspending.views.context import home
from openspending.views.entry import blueprint as entry
from openspending.views.account import blueprint as account
from openspending.views.dataset import blueprint as dataset


def register_views(app):
    app.register_blueprint(home)
    app.register_blueprint(entry)
    app.register_blueprint(account)
    app.register_blueprint(dataset)


