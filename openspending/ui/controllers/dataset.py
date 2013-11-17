from datetime import datetime
import json
import logging
from StringIO import StringIO
from urllib import urlencode

from webhelpers.feedgenerator import Rss201rev2Feed

from pylons import request, response, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n import _
from colander import SchemaNode, String, Invalid

from openspending.model import Dataset, DatasetTerritory, \
        DatasetLanguage, View, Badge, meta as db
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp
from openspending.lib.paramparser import DatasetIndexParamParser
from openspending import auth as has

from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.cache import DatasetIndexCache
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
        """
        Get a list of all datasets along with territory, language, and
        category counts (amount of datasets for each).
        """

        # Create facet filters (so we can look at a single country,
        # language etc.)
        c.query = request.params.items()
        c.add_filter = lambda f, v: '?' + urlencode(c.query +
                [(f, v)] if (f, v) not in c.query else c.query)
        c.del_filter = lambda f, v: '?' + urlencode([(k, x) for k, x in
            c.query if (k, x) != (f, v)])

        # Parse the request parameters to get them into the right format
        parser = DatasetIndexParamParser(request.params)
        params, errors = parser.parse()
        if errors:
            concatenated_errors = ', '.join(errors)
            abort(400, 
                  _('Parameter values not supported: %s') % concatenated_errors)

        # We need to pop the page and pagesize paramters since they're not
        # used for the cache (we have to get all of the datasets to do the
        # language, territory, and category counts (these are then only used
        # for the html response)
        page = params.pop('page')
        pagesize = params.pop('pagesize')

        # Get cached indices (this will also generate them if there are no
        # cached results (the cache is invalidated when a dataset is published
        # or retracted
        cache = DatasetIndexCache()
        results = cache.index(**params)

        # Generate the ETag from the last modified timestamp of the first
        # dataset (since they are ordered in descending order by last
        # modified). It doesn't matter that this happens if it has (possibly)
        # generated the index (if not cached) since if it isn't cached then
        # the ETag is definitely modified. We wrap it in a try clause since
        # if there are no public datasets we'll get an index error.
        # We also don't set c._must_revalidate to True since we don't care
        # if the index needs a hard refresh
        try:
            etag_cache_keygen(results['datasets'][0]\
                                  ['timestamps']['last_modified'])
        except IndexError:
            etag_cache_keygen(None)

        # Assign the results to template context variables
        c.language_options = results['languages']
        c.territory_options = results['territories']
        c.category_options = results['categories']

        if format == 'json':
            # Apply links to the dataset lists before returning the json
            results['datasets'] = [dataset_apply_links(r) \
                                       for r in results['datasets']]
            return to_jsonp(results)
        elif format == 'csv':
            # The CSV response only shows datasets, not languages,
            # territories, etc.
            return write_csv(results['datasets'], response)

        # If we're here then it's an html format so we show rss, do the
        # pagination and render the template
        c.show_rss = True
        # The page parameter we popped earlier is part of request.params but
        # we now know it was parsed. We have to send in request.params to
        # retain any parameters already supplied (filters)
        c.page = templating.Page(results['datasets'], items_per_page=pagesize,
                                 item_count=len(results['datasets']),
                                 **request.params)
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
        return templating.render('dataset/new.html', form_errors=dict(errors),
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
        """
        Dataset viewer. Default format is html. This will return either
        an entry index if there is no default view or the defaul view.
        If a request parameter embed is given the default view is 
        returned as an embeddable page.

        If json is provided as a format the json representation of the
        dataset is returned.
        """

        # Get the dataset (will be placed in c.dataset)
        self._get_dataset(dataset)

        # Generate the etag for the cache based on updated_at value
        etag_cache_keygen(c.dataset.updated_at)

        # Compute the number of entries in the dataset
        c.num_entries = len(c.dataset)
        
        # Handle the request for the dataset, this will return
        # a default view in c.view if there is any
        handle_request(request, c, c.dataset)

        if format == 'json':
            # If requested format is json we return the json representation
            return to_jsonp(dataset_apply_links(c.dataset.as_dict()))
        else:
            (earliest_timestamp, latest_timestamp) = c.dataset.timerange()
            if earliest_timestamp is not None:
                c.timerange = {'from': earliest_timestamp,
                               'to': latest_timestamp}

            if c.view is None:
                # If handle request didn't return a view we return the
                # entry index
                return EntryController().index(dataset, format)
            if 'embed' in request.params:
                # If embed is requested using the url parameters we return
                # a redirect to an embed page for the default view
                return redirect(h.url_for(controller='view',
                    action='embed', dataset=c.dataset.name,
                    widget=c.view.vis_widget.get('name'),
                    state=json.dumps(c.view.vis_state)))
            # Return the dataset view (for the default view)
            return templating.render('dataset/view.html')

    def about(self, dataset, format='html'):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at)
        handle_request(request, c, c.dataset)
        c.sources = list(c.dataset.sources)
        c.managers = list(c.dataset.managers)

        # Get all badges if user is admin because they can then
        # give badges to the dataset on its about page.
        if c.account and c.account.admin:
            c.badges = list(Badge.all())

        return templating.render('dataset/about.html')

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
