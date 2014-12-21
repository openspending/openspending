"""The base Controller API

Provides the BaseController class for subclassing.
"""
from time import time
import hashlib

from pylons.controllers import WSGIController
from pylons.controllers.util import etag_cache
from pylons import tmpl_context as c, request, response
from pylons import app_globals, session
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending.model import meta as db
from openspending.model.account import Account
from openspending.model.dataset import Dataset
from openspending.auth import require
from openspending.ui import i18n

import logging
log = logging.getLogger(__name__)

ACCEPT_MIMETYPES = {
    "application/json": "json",
    "text/javascript": "json",
    "application/javascript": "json",
    "text/csv": "csv"
}


def etag_cache_keygen(*a):
    """
    Generate ETag key for the cache.
    This automatically includes the username taken from the session cookie
    with the help of pylons
    """
    # Get the account name (authentication in pylons sets it to the
    # environment variable REMOTE_USER)
    account_name = request.environ.get('REMOTE_USER', None)
    etag = hashlib.sha1(repr(a) + repr(account_name)).hexdigest()
    etag_cache(etag)


def set_vary_header():
    """
    Set the vary header to force intermediate caching to be controlled by
    different request headers. This only sets Cookie as the value of the Vary
    header (because of user credentials in top navigation bar) but it could
    also include other request headers like Accept-Language if the site should
    serve different locales based on request headers.
    """
    # Set the vary header as Cookie
    response.vary = ['Cookie']

    # If ETag hasn't been generated we generate it
    if not response.etag:
        etag_cache_keygen()


class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        begin = time()
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            db.session.remove()
            db.session.close()
            log.debug("Request to %s took %sms" %
                      (request.path, int((time() - begin) * 1000)))

    def __before__(self, action, **params):
        account_name = request.environ.get('REMOTE_USER', None)
        if account_name:
            c.account = Account.by_name(account_name)
        else:
            c.account = None

        i18n.handle_request(request, c)

        c._cache_disabled = False
        c._must_revalidate = False
        c.content_section = c.dataset = None

        c.detected_l10n_languages = i18n.get_language_pairs()

    def __after__(self):
        db.session.close()
        response.pragma = None

        if not app_globals.cache_enabled or 'flash' in session._session():
            return

        if c._cache_disabled:
            return

        del response.cache_control.no_cache
        if len(session._session().keys()) == 2 and \
                not len(request.cookies.keys()):
            session._current_obj().__dict__['_sess'] = None
            response.cache_control.public = True
        else:
            response.cache_control.private = True

        # Set vary header (this will set Cookie as a value for the vary header
        # so different content can be served to logged in users
        set_vary_header()

        response.cache_control.must_revalidate = c._must_revalidate
        if not c._must_revalidate:
            response.cache_control.max_age = 3600 * 6

    def _detect_format(self, format):
        for mimetype, mimeformat in self.accept_mimetypes.items():
            if format == mimeformat or mimetype \
                    in request.headers.get("Accept", ""):
                return mimeformat
        return "html"

    def _get_dataset(self, dataset):
        c.dataset = Dataset.by_name(dataset)
        if c.dataset is None:
            abort(404, _('Sorry, there is no dataset named %r') % dataset)
        require.dataset.read(c.dataset)

    def _get_page(self, param='page'):
        try:
            return int(request.params.get(param))
        except:
            return 1
