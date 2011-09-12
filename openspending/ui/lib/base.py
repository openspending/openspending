"""The base Controller API

Provides the BaseController class for subclassing.
"""
from time import time, gmtime, strftime

from pylons.controllers import WSGIController
from pylons.templating import literal, pylons_globals
from pylons import tmpl_context as c, request, response, config, app_globals, session
from pylons.controllers.util import abort
from genshi.filters import HTMLFormFiller

from openspending import model
from openspending import mongo
from openspending.ui import i18n
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IGenshiStreamFilter, IRequest

import logging
log = logging.getLogger(__name__)

def render(template_name,
           extra_vars=None,
           form_fill=None, form_errors={},
           cache_expire=3600, cache_private=False,
           method='xhtml'):

    _setup_cache(cache_expire, cache_private)

    # Pull in extra vars if needed
    globs = extra_vars or {}

    # Second, get the globals
    globs.update(pylons_globals())
    globs['g'] = app_globals
    globs['_form_errors'] = form_errors

    # Grab a template reference
    template = globs['app_globals'].genshi_loader.load(template_name)

    stream = template.generate(**globs)

    if form_fill is not None:
        filler = HTMLFormFiller(data=form_fill)
        stream = stream | filler

    for item in PluginImplementations(IGenshiStreamFilter):
        stream = item.filter(stream)

    return literal(stream.render(method=method, encoding=None))

def _setup_cache(cache_expire, cache_private):
    del response.headers["Pragma"]

    if app_globals.debug or request.method not in ('HEAD', 'GET'):
        response.headers["Cache-Control"] = 'no-cache, no-store, max-age=0'
    else:
        response.headers["Last-Modified"] = strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())

        if cache_private:
            response.headers["Cache-Control"] = 'private, max-age=%d' % cache_expire
        else:
            response.headers["Cache-Control"] = 'public, max-age=0, s-maxage=%d' % cache_expire

class BaseController(WSGIController):

    items = PluginImplementations(IRequest)

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        begin = time()
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            mongo.connection.end_request()
            log.debug("Request to %s took %sms" % (request.path,
               int((time() - begin) * 1000)))

    def __before__(self, action, **params):
        account_name = request.environ.get('REMOTE_USER', None)
        if account_name:
            c.account = model.account.find_one_by('name', account_name)
        else:
            c.account = None

        i18n.handle_request(request, c)

        c.q = ''
        c.items_per_page = int(request.params.get('items_per_page', 20))
        c.state = session.get('state', {})

        c.datasets = list(model.dataset.find())
        c.dataset = None
        self._detect_dataset_subdomain()

        for item in self.items:
            item.before(request, c)

    def __after__(self):
        for item in self.items:
            item.after(request, c)
        if session.get('state', {}) != c.state:
            session['state'] = c.state
            session.save()

    def _detect_dataset_subdomain(self):
        http_host = request.environ.get('HTTP_HOST').lower()
        if http_host.startswith('www.'):
            http_host = http_host[len('www.'):]
        if not '.' in http_host:
            return
        dataset_name, domain = http_host.split('.', 1)
        for dataset in c.datasets:
            if dataset['name'].lower() == dataset_name:
                c.dataset = dataset

