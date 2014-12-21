from flask import current_app
from flask.ext.babel import get_locale

from openspending import auth
from openspending.i18n import get_available_locales
from openspending.views.home import blueprint as home
from openspending.views.helpers import static_path
from openspending.views.helpers import url_for


@home.before_app_request
def before_request():
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
        'static_path': static_path,
        'url_for': url_for,
        'number_symbols_group': locale.number_symbols.get('group'),
        'number_symbols_decimal': locale.number_symbols.get('decimal'),
        'site_title': current_app.config.get('SITE_TITLE'),
        'languages': languages(),
        'section_active': get_active_section(),
        'logged_in': auth.account.logged_in(),
        'can': auth,
        #'show_rss': hasattr(c, 'show_rss') and c.show_rss or None,
    }
    print data
    return data
