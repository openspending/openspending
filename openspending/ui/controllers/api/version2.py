import logging
import urllib2
import json

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, etag_cache

from openspending import auth as can
from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.source import Source
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.streaming import (JSONStreamingResponse,
                                        CSVStreamingResponse)
from solr import SolrException
from openspending.lib.jsonexport import to_jsonp, json_headers
from openspending.lib.csvexport import write_csv, csv_headers
from openspending.lib.paramparser import (AggregateParamParser,
                                          SearchParamParser)
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.base import etag_cache_keygen
from openspending.ui.lib.cache import AggregationCache
from openspending.ui.lib.hypermedia import (entry_apply_links,
                                            drilldowns_apply_links,
                                            dataset_apply_links)
from openspending.tasks.dataset import load_source
from openspending.validation.model import validate_model
from colander import Invalid

log = logging.getLogger(__name__)

__controller__ = 'APIv2Controller'


class APIv2Controller(BaseController):

    def _response_params(self, params):
        """
        Create response headers based on parameters. Headers will be something
        like "X-Drilldowns: [u'from']"
        """

        # Loop over the parameters and and add each to the response headers
        for k, v in params.items():
            # Replace both _ and - with space and then split the string on
            # whitespace, then join it together, capitalizing each part and
            # append and X. So a parameter called "this-is a_header" will
            # become X-This-Is-A-Header"
            k = k.replace('_', ' ').replace('-', ' ').split()
            k = '-'.join(['X'] + [l.capitalize() for l in k])

            # Add the header along with it's value encoded as ascii but
            # ignore all errors in encoding
            response.headers[k] = unicode(v).encode('ascii', 'ignore')

    def aggregate(self):
        """
        Aggregation of a dataset based on URL parameters. It serves the
        aggregation from a cache if possible, and if not it computes it (it's
        performed in the aggregation cache for some reason).
        """

        # Parse the aggregation parameters to get them into the right format
        parser = AggregateParamParser(request.params)
        params, errors = parser.parse()

        # If there were parsing errors we return them with status code 400
        # as jsonp, irrespective of what format was asked for.
        if errors:
            response.status = 400
            return to_jsonp({'errors': errors})

        # URL parameters are always singular nouns but we work with some
        # as plural nouns so we pop them into the plural version
        params['cuts'] = params.pop('cut')
        params['drilldowns'] = params.pop('drilldown')
        params['measures'] = params.pop('measure')

        # Get the dataset and the format and remove from the parameters
        dataset = params.pop('dataset')
        format = params.pop('format')

        # User must have the right to read the dataset to perform aggregation
        require.dataset.read(dataset)

        # Create response headers from the parameters
        self._response_params(params)

        try:
            # Create an aggregation cache for the dataset and aggregate its
            # results. The cache will perform the aggreagation if it doesn't
            # have a cached result
            cache = AggregationCache(dataset)
            result = cache.aggregate(**params)

            # If the result has drilldown we create html_url values for its
            # dimensions (linked data).
            if 'drilldown' in result:
                result['drilldown'] = drilldowns_apply_links(
                    dataset.name, result['drilldown'])

            # Do the ETag caching based on the cache_key in the summary
            # this is a weird place to do it since the heavy lifting has
            # already been performed above. TODO: Needs rethinking.
            response.last_modified = dataset.updated_at
            if cache.cache_enabled and 'cache_key' in result['summary']:
                etag_cache(result['summary']['cache_key'])

        except (KeyError, ValueError) as ve:
            # We log possible errors and return them with status code 400
            log.exception(ve)
            response.status = 400
            return to_jsonp({'errors': [unicode(ve)]})

        # If the requested format is csv we write the drilldown results into
        # a csv file and return it, if not we return a jsonp result (default)
        if format == 'csv':
            return write_csv(result['drilldown'], response,
                             filename=dataset.name + '.csv')
        return to_jsonp(result)

    def search(self):
        parser = SearchParamParser(request.params)
        params, errors = parser.parse()

        if errors:
            response.status = 400
            return to_jsonp({'errors': errors})

        expand_facets = params.pop('expand_facet_dimensions')

        format = params.pop('format')
        if format == 'csv':
            params['stats'] = False
            params['facet_field'] = None

        datasets = params.pop('dataset', None)
        if datasets is None or not datasets:
            q = Dataset.all_by_account(c.account)
            if params.get('category'):
                q = q.filter_by(category=params.pop('category'))
            datasets = q.all()
            expand_facets = False

        if not datasets:
            return {'errors': ["No dataset available."]}

        params['filter']['dataset'] = []
        for dataset in datasets:
            require.dataset.read(dataset)
            params['filter']['dataset'].append(dataset.name)

        response.last_modified = max([d.updated_at for d in datasets])
        etag_cache_keygen(parser.key(), response.last_modified)

        self._response_params(params)

        if params['pagesize'] > parser.defaults['pagesize']:

            # http://wiki.nginx.org/X-accel#X-Accel-Buffering
            response.headers['X-Accel-Buffering'] = 'no'

            if format == 'csv':
                csv_headers(response, 'entries.csv')
                streamer = CSVStreamingResponse(
                    datasets,
                    params,
                    pagesize=parser.defaults['pagesize']
                )
                return streamer.response()
            else:
                json_headers(filename='entries.json')
                streamer = JSONStreamingResponse(
                    datasets,
                    params,
                    pagesize=parser.defaults['pagesize'],
                    expand_facets=util.expand_facets
                    if expand_facets else None,
                    callback=request.params.get('callback')
                )
                return streamer.response()

        solr_browser = Browser(**params)
        try:
            solr_browser.execute()
        except SolrException as e:
            return {'errors': [unicode(e)]}

        entries = []
        for dataset, entry in solr_browser.get_entries():
            entry = entry_apply_links(dataset.name, entry)
            entry['dataset'] = dataset_apply_links(dataset.as_dict())
            entries.append(entry)

        if format == 'csv':
            return write_csv(entries, response,
                             filename='entries.csv')

        if expand_facets and len(datasets) == 1:
            facets = solr_browser.get_expanded_facets(datasets[0])
        else:
            facets = solr_browser.get_facets()

        return to_jsonp({
            'stats': solr_browser.get_stats(),
            'facets': facets,
            'results': entries
        })

    def create(self):
        """
        Adds a new dataset dynamically through a POST request
        """

        # User must be authenticated so we should have a user object in
        # c.account, if not abort with error message
        if not c.account:
            abort(status_code=400, detail='user not authenticated')

        # Check if the params are there ('metadata', 'csv_file')
        if len(request.params) != 2:
            abort(status_code=400, detail='incorrect number of params')

        metadata = request.params['metadata'] \
            if 'metadata' in request.params \
            else abort(status_code=400, detail='metadata is missing')

        csv_file = request.params['csv_file'] \
            if 'csv_file' in request.params \
            else abort(status_code=400, detail='csv_file is missing')

        # We proceed with the dataset
        try:
            model = json.load(urllib2.urlopen(metadata))
        except:
            abort(status_code=400, detail='JSON model could not be parsed')
        try:
            log.info("Validating model")
            model = validate_model(model)
        except Invalid as i:
            log.error("Errors occured during model validation:")
            for field, error in i.asdict().items():
                log.error("%s: %s", field, error)
            abort(status_code=400, detail='Model is not well formed')
        dataset = Dataset.by_name(model['dataset']['name'])
        if dataset is None:
            dataset = Dataset(model)
            require.dataset.create()
            dataset.managers.append(c.account)
            dataset.private = True  # Default value
            db.session.add(dataset)
        else:
            require.dataset.update(dataset)

        log.info("Dataset: %s", dataset.name)
        source = Source(dataset=dataset, creator=c.account, url=csv_file)

        log.info(source)
        for source_ in dataset.sources:
            if source_.url == csv_file:
                source = source_
                break
        db.session.add(source)
        db.session.commit()

        # Send loading of source into celery queue
        load_source.delay(source.id)
        return to_jsonp(dataset_apply_links(dataset.as_dict()))

    def permissions(self):
        """
        Check a user's permissions for a given dataset. This could also be
        done via request to the user, but since we're not really doing a
        RESTful service we do this via the api instead.
        """

        # Check the parameters. Since we only use one parameter we check it
        # here instead of creating a specific parameter parser
        if len(request.params) != 1 or 'dataset' not in request.params:
            return to_jsonp({'error': 'Parameter dataset missing'})

        # Get the dataset we want to check permissions for
        dataset = Dataset.by_name(request.params['dataset'])

        # Return permissions
        return to_jsonp(
            {
                "create": can.dataset.create() and dataset is None,
                "read": False if dataset is None
                else can.dataset.read(dataset),
                "update": False if dataset is None
                else can.dataset.update(dataset),
                "delete": False if dataset is None
                else can.dataset.delete(dataset)})
