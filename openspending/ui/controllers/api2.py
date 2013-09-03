import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import etag_cache

from openspending import model
from openspending import auth as can
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.streaming import JSONStreamingResponse, CSVStreamingResponse
from openspending.lib.solr_util import SolrException
from openspending.lib.jsonexport import to_jsonp, json_headers
from openspending.lib.csvexport import write_csv, csv_headers
from openspending.lib.paramparser import AggregateParamParser, SearchParamParser
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.base import etag_cache_keygen
from openspending.ui.lib.cache import AggregationCache
from openspending.ui.lib.hypermedia import entry_apply_links, \
        drilldowns_apply_links, dataset_apply_links

log = logging.getLogger(__name__)

class Api2Controller(BaseController):

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
                result['drilldown'] = drilldowns_apply_links(dataset.name,
                    result['drilldown'])

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
            q = model.Dataset.all_by_account(c.account)
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
                    expand_facets=_expand_facets if expand_facets else None,
                    callback=request.params.get('callback')
                )
                return streamer.response()

        b = Browser(**params)
        try:
            b.execute()
        except SolrException, e:
            return {'errors': [unicode(e)]}

        stats, facets, entries = b.get_stats(), b.get_facets(), b.get_entries()

        _entries = []
        for dataset, entry in entries:
            entry = entry_apply_links(dataset.name, entry)
            entry['dataset'] = dataset_apply_links(dataset.as_dict())
            _entries.append(entry)

        if format == 'csv':
            return write_csv(_entries, response,
                filename='entries.csv')

        if expand_facets and len(datasets) == 1:
            _expand_facets(facets, datasets[0])

        return to_jsonp({
            'stats': stats,
            'facets': facets,
            'results': _entries
        })


def _expand_facets(facets, dataset):
    dim_names = [d.name for d in dataset.dimensions]
    for name in facets.keys():
        if name in dim_names and dataset[name].is_compound:
            dim = dataset[name]
            member_names = [x[0] for x in facets[name]]
            facet_values = [x[1] for x in facets[name]]
            members = dim.members(dim.alias.c.name.in_(member_names))
            members = util.sort_by_reference(member_names, members, lambda x: x['name'])
            facets[name] = zip(members, facet_values)
