from pylons import config

import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending import model
from openspending import logic
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.restapi import RestAPIMixIn
from openspending.ui.lib.views import View, ViewState, handle_request
from openspending.ui.lib.authz import requires

log = logging.getLogger(__name__)

class DatasetController(BaseController, RestAPIMixIn):

    extensions = PluginImplementations(IDatasetController)

    model = model.Dataset

    def _entry_q(self, dataset):
        return  {'dataset.name': dataset.name}

    def _index_html(self, results):
        for item in self.extensions:
            item.index(c, request, response, results)

        c.results = results
        return render('dataset/index.html')

    def _make_browser(self):
        url = h.url_for(controller='dataset', action='entries',
                      id=c.dataset.name)
        c.browser = Browser(request.params, dataset_name=c.dataset.name,
                            url=url)
        c.browser.facet_by_dimensions()

    def _view_html(self, dataset):
        c.dataset = dataset

        # TODO: make this a method
        entry_query = self._entry_q(dataset)
        c.num_entries = logic.entry.count(**entry_query)
        c.template = 'dataset/view.html'

        handle_request(request, c, c.dataset)
        if c.view is None:
            self._make_browser()

        for item in self.extensions:
            item.read(c, request, response, c.dataset)

        return render(c.template)

    def entries(self, id=None, format='html'):
        c.dataset = model.Dataset.by_id(id)
        if not c.dataset:
            abort(404, _('Sorry, there is no dataset named %r') % id)
        self._make_browser()

        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
            return

        return render('dataset/entries.html')

    def explorer(self, id=None):
        c.dataset = model.Dataset.by_id(id)
        c.keys_meta = dict([(k.key, {"label": k.label,
                "description": k.get("description", "")})
                for k in model.Dimension.find({"dataset": c.dataset.name})])
        if "breakdownKeys" in c.dataset:
            c.breakdown_keys = c.dataset["breakdownKeys"]
        else:
            c.breakdown_keys = c.keys_meta.keys()[:3]

        c.keys_meta_json = json.dumps(c.keys_meta)
        c.breakdown_keys_json = json.dumps(c.breakdown_keys)
        return render('dataset/explorer.html')

    def timeline(self, id):
        c.dataset = model.Dataset.by_id(id)
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

    @requires("admin")
    def dropdb(self):
        if config.get('openspending.sandbox_mode') != 'true':
            abort(403, "Deleting the database is not permitted unless in sandbox mode")
            return

        from openspending import mongo
        mongo.drop_collections()
        return render('dataset/dropdb.html')
