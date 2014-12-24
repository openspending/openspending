from flask import current_app, request
from flask.ext.babel import get_locale
from flask.ext.login import current_user

from openspending import auth
from openspending.i18n import get_available_locales
from openspending.views.home import blueprint as home
from openspending.lib.helpers import static_path
from openspending.lib.helpers import url_for


@home.before_app_request
def before_request():
    request._ds_available_views = []
    request._ds_view = None


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
    # ["blog", "dataset", "search", "resources", "help", "about"]
    return {'dataset': True}


@home.app_context_processor
def template_context_processor():
    locale = get_locale()
    data = {
        'DEBUG': current_app.config.get('DEBUG'),
        'current_language': locale.language,
        'current_locale': get_locale(),
        'static_path': static_path,
        'url_for': url_for,
        'site_url': url_for('home.index').rstrip('/'),
        'number_symbols_group': locale.number_symbols.get('group'),
        'number_symbols_decimal': locale.number_symbols.get('decimal'),
        'site_title': current_app.config.get('SITE_TITLE'),
        'languages': languages(),
        'section_active': get_active_section(),
        'logged_in': auth.account.logged_in(),
        'current_user': current_user,
        'can': auth,
        'legacy_views': {
            'available': request._ds_available_views,
            'active': request._ds_view,
        }
    }
    return data

# def etag_cache_keygen(*a):
#     """
#     Generate ETag key for the cache.
#     This automatically includes the username taken from the session cookie
#     with the help of pylons
#     """
#     # Get the account name (authentication in pylons sets it to the
#     # environment variable REMOTE_USER)
#     account_name = request.environ.get('REMOTE_USER', None)
#     etag = hashlib.sha1(repr(a) + repr(account_name)).hexdigest()
#     etag_cache(etag)


# def set_vary_header():
#     """
#     Set the vary header to force intermediate caching to be controlled by
#     different request headers. This only sets Cookie as the value of the Vary
#     header (because of user credentials in top navigation bar) but it could
#     also include other request headers like Accept-Language if the site should
#     serve different locales based on request headers.
#     """
#     # Set the vary header as Cookie
#     response.vary = ['Cookie']

#     # If ETag hasn't been generated we generate it
#     if not response.etag:
#         etag_cache_keygen()


# class BaseController(WSGIController):

#     def __call__(self, environ, start_response):
#         """Invoke the Controller"""
#         # WSGIController.__call__ dispatches to the Controller method
#         # the request is routed to. This routing information is
#         # available in environ['pylons.routes_dict']
#         begin = time()
#         try:
#             return WSGIController.__call__(self, environ, start_response)
#         finally:
#             db.session.remove()
#             db.session.close()
#             log.debug("Request to %s took %sms" %
#                       (request.path, int((time() - begin) * 1000)))

#     def __before__(self, action, **params):
#         account_name = request.environ.get('REMOTE_USER', None)
#         if account_name:
#             c.account = Account.by_name(account_name)
#         else:
#             c.account = None

#         i18n.handle_request(request, c)

#         c._cache_disabled = False
#         c._must_revalidate = False
#         c.content_section = c.dataset = None

#         c.detected_l10n_languages = i18n.get_language_pairs()

#     def __after__(self):
#         db.session.close()
#         response.pragma = None

#         if not app_globals.cache_enabled or 'flash' in session._session():
#             return

#         if c._cache_disabled:
#             return

#         del response.cache_control.no_cache
#         if len(session._session().keys()) == 2 and \
#                 not len(request.cookies.keys()):
#             session._current_obj().__dict__['_sess'] = None
#             response.cache_control.public = True
#         else:
#             response.cache_control.private = True

#         # Set vary header (this will set Cookie as a value for the vary header
#         # so different content can be served to logged in users
#         set_vary_header()

#         response.cache_control.must_revalidate = c._must_revalidate
#         if not c._must_revalidate:
#             response.cache_control.max_age = 3600 * 6
