import logging
from urllib import urlencode

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import SchemaNode, String, Invalid

from openspending.model import Dataset, DatasetTerritory, \
        DatasetLanguage, meta as db
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
from openspending.reference.country import COUNTRIES
from openspending.reference.language import LANGUAGES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.common import ValidationState
from openspending.ui.controllers.entry import EntryController

log = logging.getLogger(__name__)

class DatasetController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    def index(self, format='html'):
        for item in self.extensions:
            item.index(c, request, response, c.results)

        c.query = request.params.items()
        c.add_filter = lambda f, v: '?' + urlencode(c.query +
                [(f, v)] if (f, v) not in c.query else c.query)
        c.del_filter = lambda f, v: '?' + urlencode([(k,x) for k, x in
            c.query if (k,x) != (f,v)])
        c.results = c.datasets
        for language in request.params.getall('languages'):
            l = db.aliased(DatasetLanguage)
            c.results = c.results.join(l, Dataset._languages)
            c.results = c.results.filter(l.code==language)
        for territory in request.params.getall('territories'):
            t = db.aliased(DatasetTerritory)
            c.results = c.results.join(t, Dataset._territories)
            c.results = c.results.filter(t.code==territory)
        c.results = list(c.results)
        c.territory_options = [{'code': code,
                                'count': count,
                                'url': h.url_for(controller='dataset',
                                    action='index', territories=code),
                                'label': COUNTRIES.get(code, code)} \
            for (code, count) in DatasetTerritory.dataset_counts(c.results)]
        c.language_options = [{'code': code,
                               'count': count,
                               'url': h.url_for(controller='dataset',
                                    action='index', languages=code),
                               'label': LANGUAGES.get(code, code)} \
            for (code, count) in DatasetLanguage.dataset_counts(c.results)]

        if format == 'json':
            results = map(lambda d: d.as_dict(), c.results)
            return to_jsonp({
                'datasets': results,
                'territories': c.territory_options,
                'languages': c.language_options
                })
        elif format == 'csv':
            results = map(lambda d: d.as_dict(), c.results)
            return write_csv(results, response)
        return render('dataset/index.html')

    def cta(self):
        return render('dataset/new_cta.html')

    def new(self, errors={}):
        c.key_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if k], 
                key=lambda (k, v): v)
        c.all_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if not k], 
                key=lambda (k, v): v)
        c.languages = sorted(LANGUAGES.items(), key=lambda (k, v): v)
        c.territories = sorted(COUNTRIES.items(), key=lambda (k, v): v)
        require.account.create()
        errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
        c.have_error = bool(errors)
        c.dataset_info_style = '' if errors else 'display: none;'
        return render('dataset/new.html', form_errors=dict(errors),
                form_fill=request.params if errors else {'currency': 'USD'})

    def create(self):
        require.account.create()
        try:
            dataset = dict(request.params)
            dataset['territories'] = request.params.getall('territories')
            dataset['languages'] = request.params.getall('languages')
            model = {'dataset': dataset}
            schema = dataset_schema(ValidationState(model))
            data = schema.deserialize(dataset)
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

    def embed(self, dataset):
        return render('dataset/embed.html')
