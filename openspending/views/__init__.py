from openspending.lib import filters
from openspending.i18n import get_locale

from openspending.views.context import home
from openspending.views.cache import NotModified, handle_not_modified

from openspending.views.entry import blueprint as entry
from openspending.views.account import blueprint as account
from openspending.views.dataset import blueprint as dataset
from openspending.views.badge import blueprint as badge
from openspending.views.view import blueprint as view
from openspending.views.editor import blueprint as editor
from openspending.views.source import blueprint as source
from openspending.views.run import blueprint as run
from openspending.views.api import blueprint as api
from openspending.views.dimension import blueprint as dimension
from openspending.views.error import handle_error


def register_views(app, babel):
    babel.locale_selector_func = get_locale

    app.register_blueprint(home)
    app.register_blueprint(entry)
    app.register_blueprint(account)
    app.register_blueprint(dataset)
    app.register_blueprint(badge)
    app.register_blueprint(view)
    app.register_blueprint(editor)
    app.register_blueprint(source)
    app.register_blueprint(run)
    app.register_blueprint(api)
    app.register_blueprint(dimension)

    app.error_handler_spec[None][400] = handle_error
    app.error_handler_spec[None][401] = handle_error
    app.error_handler_spec[None][402] = handle_error
    app.error_handler_spec[None][403] = handle_error
    app.error_handler_spec[None][404] = handle_error
    app.error_handler_spec[None][500] = handle_error

    app.error_handler_spec[None][NotModified] = handle_not_modified

    app.jinja_env.filters.update({
        'markdown_preview': filters.markdown_preview,
        'markdown': filters.markdown,
        'format_currency': filters.format_currency,
        'readable_url': filters.readable_url,
        'entry_description': filters.entry_description,
        'render_value': filters.render_value
    })

