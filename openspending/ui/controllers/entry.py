import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.i18n import _

from openspending.ui.lib.base import BaseController, render, \
        sitemap, etag_cache_keygen
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.hypermedia import entry_apply_links
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_json, to_jsonp
from openspending.ui.lib import helpers as h
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)


class EntryController(BaseController):

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)

        if format in ['json', 'csv']:
            return redirect(h.url_for(controller='api2', action='search',
                format=format, dataset=dataset,
                **request.params))

        handle_request(request, c, c.dataset)
        return templating.render('entry/index.html')

    def view(self, dataset, id, format='html'):
        self._get_dataset(dataset)
        entries = list(c.dataset.entries(c.dataset.alias.c.id == id))
        if not len(entries) == 1:
            abort(404, _('Sorry, there is no entry %r') % id)
        c.entry = entry_apply_links(dataset, entries.pop())

        c.id = c.entry.get('id')
        c.from_ = c.entry.get('from')
        c.to = c.entry.get('to')
        c.currency = c.entry.get('currency', c.dataset.currency).upper()
        c.amount = c.entry.get('amount')
        c.time = c.entry.get('time')

        c.custom_html = h.render_entry_custom_html(c.dataset,
                                                   c.entry)

        excluded_keys = ('time', 'amount', 'currency', 'from',
                         'to', 'dataset', 'id', 'name', 'description')

        c.extras = {}
        if c.dataset:
            c.desc = dict([(d.name, d) for d in c.dataset.dimensions])
            for key in c.entry:
                if key in c.desc and \
                        not key in excluded_keys:
                    c.extras[key] = c.entry[key]

        if format == 'json':
            return to_jsonp(c.entry)
        elif format == 'csv':
            return write_csv([c.entry], response)
        else:
            return templating.render('entry/view.html')

    def search(self):
        c.content_section = 'search'
        return templating.render('entry/search.html')

    def sitemap(self, dataset, page):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at, 'xml')
        limit = 30000
        pages = []
        for entry in c.dataset.entries(limit=limit,
                                       offset=(int(page) - 1) * limit,
                                       step=limit, fields=[]):
            pages.append({
                'loc': h.url_for(controller='entry', action='view',
                                 dataset=dataset, id=entry.get('id'),
                                 qualified=True),
                'lastmod': c.dataset.updated_at
                })
        return sitemap(pages)
