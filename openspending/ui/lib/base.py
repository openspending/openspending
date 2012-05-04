"""The base Controller API

Provides the BaseController class for subclassing.
"""
from time import time, gmtime, strftime
from datetime import datetime, timedelta
import hashlib

from pylons.controllers import WSGIController
from pylons.templating import literal, pylons_globals
from pylons.controllers.util import etag_cache
from pylons import tmpl_context as c, request, response, config
from pylons import app_globals, session
from pylons.controllers.util import abort
from genshi.filters import HTMLFormFiller
from pylons.i18n import _

from openspending.model import meta as db
from openspending.auth import require
import openspending.auth as can
from openspending import model
from openspending.ui import i18n

import logging
log = logging.getLogger(__name__)

ACCEPT_MIMETYPES = {
    "application/json": "json",
    "text/javascript": "json",
    "application/javascript": "json",
    "text/csv": "csv"
}

def render(template_name,
           extra_vars=None,
           form_fill=None, form_errors={},
           method='xhtml'):

    # Pull in extra vars if needed
    globs = extra_vars or {}

    # Second, get the globals
    globs.update(pylons_globals())
    globs['g'] = app_globals
    globs['can'] = can
    globs['_form_errors'] = form_errors

    # Grab a template reference
    template = globs['app_globals'].genshi_loader.load(template_name)

    stream = template.generate(**globs)

    if form_fill is not None:
        filler = HTMLFormFiller(data=form_fill)
        stream = stream | filler

    return literal(stream.render(method=method, encoding=None))


def etag_cache_keygen(*a):
    etag = hashlib.sha1(repr(a)).hexdigest()
    etag_cache(etag)


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
            log.debug("Request to %s took %sms" % (request.path,
               int((time() - begin) * 1000)))

    def __before__(self, action, **params):
        account_name = request.environ.get('REMOTE_USER', None)
        if account_name:
            c.account = model.Account.by_name(account_name)
        else:
            c.account = None

        i18n.handle_request(request, c)

        c._cache_disabled = False
        c.datasets = model.Dataset.all_by_account(c.account)
        c.dataset = None

        c.detected_l10n_languages = i18n.get_language_pairs()

    def __after__(self):
        db.session.close()
        response.pragma = None

        if not app_globals.cache_enabled or 'flash' in session._session():
            return

        if c._cache_disabled:
            return

        del response.cache_control.no_cache
        if len(session._session().keys()) == 2 and not len(request.cookies.keys()):
            session._current_obj().__dict__['_sess'] = None
            response.cache_control.public = True
        else:
            response.cache_control.private = True
        response.cache_control.max_age = 3600
        response.last_modified = response.last_modified or datetime.utcnow()
        response.expires = datetime.utcnow() + \
            timedelta(seconds=response.cache_control.max_age)

    def _detect_format(self, format):
        for mimetype, mimeformat in self.accept_mimetypes.items():
            if format == mimeformat or \
                    mimetype in request.headers.get("Accept", ""):
                return mimeformat
        return "html"

    def _disable_cache(self):
        c._cache_disabled = True

    def _get_dataset(self, dataset):
        c.dataset = model.Dataset.by_name(dataset)
        if c.dataset is None:
            abort(404, _('Sorry, there is no dataset named %r') % dataset)
        require.dataset.read(c.dataset)

    def _get_page(self, param='page'):
        try:
            return int(request.params.get(param))
        except:
            return 1
