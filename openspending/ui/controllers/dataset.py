from datetime import datetime
import json
import logging
from StringIO import StringIO
from urllib import urlencode

from webhelpers.feedgenerator import Rss201rev2Feed

from pylons import request, response, tmpl_context as c, url
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import SchemaNode, String, Invalid

from openspending.model import Dataset, DatasetTerritory, \
        DatasetLanguage, View, meta as db
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp
from openspending import auth as has

from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render, sitemap
from openspending.ui.lib.base import require, etag_cache_keygen
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.hypermedia import dataset_apply_links
from openspending.reference.currency import CURRENCIES
from openspending.reference.country import COUNTRIES
from openspending.reference.category import CATEGORIES
from openspending.reference.language import LANGUAGES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.common import ValidationState
from openspending.ui.controllers.entry import EntryController
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)


class DatasetController(BaseController):

    def index(self, format='html'):
        c.query = request.params.items()
        c.add_filter = lambda f, v: '?' + urlencode(c.query +
                [(f, v)] if (f, v) not in c.query else c.query)
        c.del_filter = lambda f, v: '?' + urlencode([(k, x) for k, x in
            c.query if (k, x) != (f, v)])
        c.results = c.datasets
        for language in request.params.getall('languages'):
            l = db.aliased(DatasetLanguage)
            c.results = c.results.join(l, Dataset._languages)
            c.results = c.results.filter(l.code == language)
        for territory in request.params.getall('territories'):
            t = db.aliased(DatasetTerritory)
            c.results = c.results.join(t, Dataset._territories)
            c.results = c.results.filter(t.code == territory)
        category = request.params.get('category')
        if category:
            c.results = c.results.filter(Dataset.category == category)

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

        # TODO: figure out where to put this:
        ds_ids = [d.id for d in c.results]
        if len(ds_ids):
            q = db.select([Dataset.category, db.func.count(Dataset.id)],
                Dataset.id.in_(ds_ids), group_by=Dataset.category,
                order_by=db.func.count(Dataset.id).desc())
            c.category_options = [{'category': category,
                                   'count': count,
                                   'url': h.url_for(controller='dataset',
                                        action='index', category=category),
                                   'label': CATEGORIES.get(category, category)} \
                for (category, count) in db.session.bind.execute(q).fetchall() \
                if category is not None]
        else:
            c.category_options = []

        c._must_revalidate = True
        if len(c.results):
            dt = max([r.updated_at for r in c.results])
            etag_cache_keygen(dt)

        if format == 'json':
            results = map(lambda d: d.as_dict(), c.results)
            results = [dataset_apply_links(r) for r in results]
            return to_jsonp({
                'datasets': results,
                'categories': c.category_options,
                'territories': c.territory_options,
                'languages': c.language_options
                })
        elif format == 'csv':
            results = map(lambda d: d.as_dict(), c.results)
            return write_csv(results, response)
        c.show_rss = True
        return templating.render('dataset/index.html')

    def new(self, errors={}):
        self._disable_cache()
        if not has.dataset.create():
            return templating.render('dataset/new_cta.html')
        require.dataset.create()
        c.key_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if k],
                key=lambda (k, v): v)
        c.all_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if not k],
                key=lambda (k, v): v)
        c.languages = sorted(LANGUAGES.items(), key=lambda (k, v): v)
        c.territories = sorted(COUNTRIES.items(), key=lambda (k, v): v)
        c.categories = sorted(CATEGORIES.items(), key=lambda (k, v): v)
        errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
        return render('dataset/new.html', form_errors=dict(errors),
                form_fill=request.params if errors else {'currency': 'USD'})

    def create(self):
        require.dataset.create()
        try:
            dataset = dict(request.params)
            dataset['territories'] = request.params.getall('territories')
            dataset['languages'] = request.params.getall('languages')
            model = {'dataset': dataset}
            schema = dataset_schema(ValidationState(model))
            data = schema.deserialize(dataset)
            if Dataset.by_name(data['name']) is not None:
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
        etag_cache_keygen(c.dataset.updated_at)
        c.num_entries = len(c.dataset)
        handle_request(request, c, c.dataset)


        if format == 'json':
            return to_jsonp(dataset_apply_links(c.dataset.as_dict()))
        else:
            if c.view is None:
                return EntryController().index(dataset, format)
            if 'embed' in request.params:
                return redirect(h.url_for(controller='view',
                    action='embed', dataset=c.dataset.name,
                    widget=c.view.vis_widget.get('name'),
                    state=json.dumps(c.view.vis_state)))
            return templating.render('dataset/view.html')

    def about(self, dataset, format='html'):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at)
        handle_request(request, c, c.dataset)
        c.sources = list(c.dataset.sources)
        c.managers = list(c.dataset.managers)
        return templating.render('dataset/about.html')

    def sitemap(self, dataset):
        self._get_dataset(dataset)
        pages = []
        for action in ['view', 'about']:
            pages.append({
                'loc': h.url_for(controller='dataset', action=action,
                                 dataset=c.dataset.name, qualified=True),
                'lastmod': c.dataset.updated_at,
                'priority': 0.8})
        for view in View.all_by_dataset(c.dataset):
            pages.append({
                'loc': h.url_for(controller='view', action='view',
                                 dataset=dataset, name=view.name,
                                 qualified=True),
                'lastmod': view.updated_at
                })
        return sitemap(pages)

    def explorer(self, dataset):
        redirect(h.url_for(controller='view', action='new',
                           dataset=dataset))

    def model(self, dataset, format='json'):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at)
        model = c.dataset.model
        model['dataset'] = dataset_apply_links(model['dataset'])
        return to_jsonp(model)

    def feed_rss(self):
        q = db.session.query(Dataset)
        if not (c.account and c.account.admin):
            q = q.filter_by(private = False)
        feed_items = q.order_by(Dataset.created_at.desc()).limit(20)
        items = []
        for feed_item in feed_items:
            items.append({
                'title': feed_item.label,
                'pubdate': feed_item.updated_at,
                'link': url(controller='dataset', action='view',
                    dataset=feed_item.name, qualified=True),
                'description': feed_item.description,
                'author_name': ', '.join([person.fullname for person in
                                          feed_item.managers if
                                          person.fullname]),
                })
        feed = Rss201rev2Feed(_('Recently Created Datasets'), url(
            controller='home', action='index', qualified=True), _('Recently '
            'created datasets in the OpenSpending Platform'),
            author_name='Openspending')
        for item in items:
            feed.add_item(**item)
        sio = StringIO()
        feed.write(sio, 'utf-8')
        response.content_type = 'application/xml'
        return sio.getvalue()
