from flask import current_app, request
from flask.ext.babel import get_locale

from openspending import auth
from openspending.i18n import get_available_locales
from openspending.views.home import blueprint as home
from openspending.views.entry import blueprint as entry
from openspending.views.account import blueprint as account
from openspending.views.dataset import blueprint as dataset


@home.before_app_request
def before_request():
    #i18n.handle_request(request)
    pass


def languages():
    current_locale = get_locale()

    def details(locale):
        return {
            "lang_code": locale.language,
            "lang_name": locale.language_name,
            "current_locale": locale == current_locale
        }
    return [details(l) for l in get_available_locales()]


def get_active_section():
    # TODO: use request.endpoint
    return 'home'


@home.app_context_processor
def template_context_processor():
    locale = get_locale()
    data = {
        'DEBUG': current_app.config.get('DEBUG'),
        'current_language': locale.language,
        'current_locale': get_locale(),
        #'script_root': h.script_root(),
        #'script_boot': h.script_tag('prod/boot'),
        #'bootstrap_css': h.static('style/bootstrap.css'),
        #'style_css': h.static('style/style.css'),
        'number_symbols_group': locale.number_symbols.get('group'),
        'number_symbols_decimal': locale.number_symbols.get('decimal'),
        'site_title': current_app.config.get('SITE_TITLE'),
        #'static': config.get('openspending.static_path', '/static/'),
        'static_cache_version': 'no_version',
        'languages': languages(),
        'section_active': get_active_section(),
        'logged_in': auth.account.logged_in(),
        'can': auth,
        #'show_rss': hasattr(c, 'show_rss') and c.show_rss or None,
    }
    print data
    return data


def register_views(app):
    app.register_blueprint(home)
    app.register_blueprint(entry)
    app.register_blueprint(account)
    app.register_blueprint(dataset)


