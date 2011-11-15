import logging

from pylons import request, response, tmpl_context as c
from pylons.i18n import _

from openspending import model
from openspending.model import meta as db
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render, abort
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.views import View, ViewState, handle_request
from openspending.ui.lib.color import rgb_rainbow

log = logging.getLogger(__name__)

class DatasetController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    model = model.Dataset

    def index(self, format='html'):
        c.results = model.Dataset.all_by_account(c.account)
        for item in self.extensions:
            item.index(c, request, response, c.results)

        if format == 'json':
            return to_jsonp(map(lambda d: d.as_dict(),
                                c.results))
        elif format == 'csv':
            results = map(lambda d: d.as_dict(), c.results)
            return write_csv(results, response)
        else:
            return render('dataset/index.html')

    def view(self, dataset, format='html'):
        self._get_dataset(dataset)
        c.num_entries = len(c.dataset)

        handle_request(request, c, c.dataset)

        if c.view is None:
            url = h.url_for(controller='entry', action='index',
                        dataset=c.dataset.name)
            c.browser = Browser(c.dataset, request.params, url=url)
            c.browser.facet_by_dimensions()

        for item in self.extensions:
            item.read(c, request, response, c.dataset)

        if format == 'json':
            return to_jsonp(c.dataset.as_dict())
        elif format == 'csv':
            return write_csv([c.dataset.as_dict()], response)
        else:
            return render('dataset/view.html')

    def old_explorer(self, name=None):
        self._get_dataset(name)
        c.keys_meta = dict([(d.name, {"label": d.label,
                "description": d.description})
                for d in c.dataset.dimensions])
        c.breakdown_keys = c.keys_meta.keys()[:3]
        c.keys_meta_json = json.dumps(c.keys_meta)
        c.breakdown_keys_json = json.dumps(c.breakdown_keys)
        return render('dataset/explorer.html')

#    def bubbles(self, name, breakdown_field, drilldown_fields, format="html"):
    def explorer(self, dataset, aggregation_url):
        aggregation_url = aggregation_url.lstrip('/')
        parts = aggregation_url.split('/')
        breakdown_field = parts[0] if parts else None
        drilldown_fields = parts[1] if len(parts) > 1 else ''
        c.drilldown_fields = json.dumps(drilldown_fields.split(','))
        self._get_dataset(dataset)
        c.dataset_name = c.dataset.name

#        try:
#            results = c.dataset.aggregate(drilldowns=[breakdown_field])
#        except KeyError:
#            abort(404, "Dimension `%s' not available" % breakdown_field)
#
#        log.info(results)
#        breakdowns = results['drilldown']
#        breakdown_names = [ i[breakdown_field]['label'] for i in breakdowns ]
#
#        count = len(breakdown_names)
#
#        styles = [ s for s in rgb_rainbow(count) ]
#        breakdown_styles = dict([ (breakdown_names[n], styles[n]) for n in range(0, count) ])
#        c.breakdown_styles = [ "'%s' : { color: '%s' }," % (k, v) for k, v in breakdown_styles.iteritems() ]
        c.breakdown_field = breakdown_field

        # handle_request(request, c, c.dataset)

        # TODO: make this a method
        # c.template = 'dataset/view_bubbles.html'
        # return render(c.template)
        return render('dataset/explorer.html')

    def model(self, dataset, format='json'):
        self._get_dataset(dataset)
        return to_jsonp(c.dataset.data)

    def timeline(self, name):
        self._get_dataset(name)
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

