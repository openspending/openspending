import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import SchemaNode, String, Invalid


from openspending.model import Dataset, meta as db
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import require
from openspending.ui.lib.views import View, ViewState, handle_request
from openspending.reference.currency import CURRENCIES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.common import ValidationState
from openspending.ui.controllers.entry import EntryController

log = logging.getLogger(__name__)

class DatasetController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    def index(self, format='html'):
        for item in self.extensions:
            item.index(c, request, response, c.results)

        if format == 'json':
            return to_jsonp(map(lambda d: d.as_dict(),
                                c.datasets))
        elif format == 'csv':
            results = map(lambda d: d.as_dict(), c.datasets)
            return write_csv(results, response)
        else:
            return render('dataset/index.html')

    def cta(self):
        return render('dataset/new_cta.html')

    def new(self, errors={}):
        c.currencies = sorted(CURRENCIES.items(), key=lambda (k,v): v)
        require.account.create()
        errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
        return render('dataset/new.html', form_errors=dict(errors),
                form_fill=request.params if errors else {'currency': 'USD'})

    def create(self):
        require.account.create()
        try:
            model = {'dataset': request.params}
            schema = dataset_schema(ValidationState(model))
            data = schema.deserialize(request.params)
            if Dataset.by_name(data['name']):
                raise Invalid(SchemaNode(String(), name='dataset.name'),
                    _("A dataset with this identifer already exists!"))
            dataset = Dataset({'dataset': data})
            dataset.private = True
            dataset.managers.append(c.account)
            db.session.add(dataset)
            db.session.commit()
            redirect(h.url_for(controller='editor', action='index', 
                               dataset=dataset.name))
        except Invalid, i:
            errors = i.asdict()
            return self.new(errors)

    def view(self, dataset, format='html'):
        self._get_dataset(dataset)
        c.num_entries = len(c.dataset)

        handle_request(request, c, c.dataset)

        if c.view is None and format == 'html':
            return EntryController().index(dataset, format)

        for item in self.extensions:
            item.read(c, request, response, c.dataset)

        if format == 'json':
            return to_jsonp(c.dataset.as_dict())
        elif format == 'csv':
            return write_csv([c.dataset.as_dict()], response)
        else:
            return render('dataset/view.html')

    def about(self, dataset, format='html'):
        self._get_dataset(dataset)
        handle_request(request, c, c.dataset)
        c.sources = list(c.dataset.sources)
        c.managers = list(c.dataset.managers)
        return render('dataset/about.html')

    def explorer(self, dataset):
        self._get_dataset(dataset)
        c.dataset_name = c.dataset.name
        return render('dataset/explorer.html')

    def model(self, dataset, format='json'):
        self._get_dataset(dataset)
        return to_jsonp(c.dataset.model)

    def timeline(self, name):
        self._get_dataset(name)
        c.dataset = Dataset.by_name(name)
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

