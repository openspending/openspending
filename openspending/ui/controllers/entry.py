import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.i18n import _
from routes import url_for

from openspending import model
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IEntryController
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.browser import Browser
from openspending.ui.lib import helpers as h

log = logging.getLogger(__name__)

class EntryController(BaseController):

    extensions = PluginImplementations(IEntryController)
    
    def index(self, dataset, format='html'):
        c.dataset = model.Dataset.by_name(dataset)
        if not c.dataset:
            abort(404, _('Sorry, there is no dataset named %r') % dataset)
        url = h.url_for(controller='entry', action='index',
                    dataset=c.dataset.name)
        c.browser = Browser(c.dataset, request.params, url=url)
        c.browser.facet_by_dimensions()

        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
            return
        else:
            return render('dataset/entries.html')

    def _view_html(self, entry):
        c.entry = entry

        c.id = c.entry.get('_id')
        c.from_ = c.entry.get('from')
        c.to = c.entry.get('to')
        c.dataset = model.entry.get_dataset(entry)
        c.currency = c.entry.get('currency', c.dataset.get('currency')).upper()
        c.amount = c.entry.get('amount')
        c.time = c.entry.get('time')

        c.custom_html = model.dataset.render_entry_custom_html(c.dataset, c.entry)

        excluded_keys = ('time', 'amount', 'currency', 'from',
                         'to', 'dataset', '_id', 'classifiers', 'name',
                         'classifier_ids', 'description')

        c.extras = {}
        if c.dataset:
            dataset_name = c.dataset["name"]
            dimensions = model.dimension.get_dataset_dimensions(dataset_name)
            c.desc = dict([(d.get('key'), d) for d in dimensions])
            for key in c.entry:
                if key in c.desc and \
                        not key in excluded_keys:
                    c.extras[key] = c.entry[key]

        c.template = 'entry/view.html'

        for item in self.extensions:
            item.read(c, request, response, c.entry)

        return render(c.template)

