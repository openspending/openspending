from pylons import config

import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending import model
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.restapi import RestAPIMixIn
from openspending.ui.lib.views import View, ViewState, handle_request
from openspending.ui.lib.authz import requires
from openspending.ui.lib.color import rgb_rainbow

log = logging.getLogger(__name__)

class DatasetController(BaseController, RestAPIMixIn):

    extensions = PluginImplementations(IDatasetController)

    model = model.Dataset

    def view(self, name, format="html"):
        d = model.Dataset.by_name(name)
        return self._view(dataset=d, format=format)

    def bubbles(self, name, breakdown_field, drilldown_fields, format="html"):
        c.drilldown_fields = json.dumps(drilldown_fields.split(','))
        c.dataset = model.Dataset.by_name(name)
        c.dataset_name = name

        # TODO: make this a method
        c.template = 'dataset/view_bubbles.html'

        curs = model.entry.find({'dataset.name':name})# , {breakdown_field: True})
        breakdown_names = list(set([ i[breakdown_field]['name'] for i in curs ]))

        count = len(breakdown_names)

        styles = [ s for s in rgb_rainbow(count) ]
        breakdown_styles = dict([ (breakdown_names[n], styles[n]) for n in range(0, count) ])
        c.breakdown_styles = [ "'%s' : { color: '%s' }," % (k, v) for k, v in breakdown_styles.iteritems() ]
        c.breakdown_field = breakdown_field

        handle_request(request, c, c.dataset)
        if c.view is None:
            self._make_browser()

        if hasattr(c, 'time'):
            delattr(c, 'time') # disable treemap(!)

        return render(c.template)

    def _entry_q(self, dataset):
        return  {'dataset': dataset.name}

    def _index_html(self, results):
        for item in self.extensions:
            item.index(c, request, response, results)

        c.results = results
        return render('dataset/index.html')

    def _make_browser(self):
        url = h.url_for(controller='dataset', action='entries',
                        name=c.dataset.name)
        c.browser = Browser(request.params, dataset=c.dataset,
                            url=url)
        c.browser.facet_by_dimensions()

    def _view_html(self, dataset):
        c.dataset = dataset

        c.num_entries = model.entry.find({'dataset.name': dataset['name']}).count()

        handle_request(request, c, c.dataset)

        if c.view is None:
            self._make_browser()

        for item in self.extensions:
            item.read(c, request, response, c.dataset)

        return render('dataset/view.html')

    def entries(self, name, format='html'):
        c.dataset = model.Dataset.by_name(name)
        if not c.dataset:
            abort(404, _('Sorry, there is no dataset named %r') % name)
        self._make_browser()

        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
        else:
            return self._entries_html()

    def _entries_html(self):
        return render('dataset/entries.html')

    def explorer(self, name=None):
        c.dataset = model.Dataset.by_name(name)
        c.keys_meta = dict([(d.name, {"label": d.label,
                "description": d.description})
                for d in c.dataset.dimensions])
        c.breakdown_keys = c.keys_meta.keys()[:3]
        c.keys_meta_json = json.dumps(c.keys_meta)
        c.breakdown_keys_json = json.dumps(c.breakdown_keys)
        return render('dataset/explorer.html')

    def timeline(self, name):
        c.dataset = model.Dataset.by_name(name)
        view = View.by_name(c.dataset, "default")
        viewstate = ViewState(c.dataset, view, None)
        data = []
        meta = []
        for entry, year_data in viewstate.aggregates:
            meta.append({"label": entry.get("label"),
                         "description": entry.get("description", ""),
                         "name": entry.get("name"),
                         "index": len(meta),
                         "taxonomy": entry.get("taxonomy")})
            sorted_year_data = sorted(year_data.items(), key=lambda kv: kv[0])
            data.append([{"x": k, "y": v,
                          "meta": len(meta) - 1} for
                         k, v in sorted_year_data])
        c.data = json.dumps(data)
        c.meta = json.dumps(meta)
        return render('dataset/timeline.html')

