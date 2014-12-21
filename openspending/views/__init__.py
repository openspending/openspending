from openspending.views.context import home
from openspending.views.entry import blueprint as entry
from openspending.views.account import blueprint as account
from openspending.views.dataset import blueprint as dataset
from openspending.views.error import handle_error


def register_views(app):
    app.register_blueprint(home)
    app.register_blueprint(entry)
    app.register_blueprint(account)
    app.register_blueprint(dataset)

    app.error_handler_spec[None][400] = handle_error
    app.error_handler_spec[None][401] = handle_error
    app.error_handler_spec[None][402] = handle_error
    app.error_handler_spec[None][403] = handle_error
    app.error_handler_spec[None][404] = handle_error
    app.error_handler_spec[None][500] = handle_error


