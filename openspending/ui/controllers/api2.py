import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import etag_cache

from openspending import model
from openspending.lib.browser import Browser
from openspending.lib.jsonexport import jsonpify
from openspending.lib.paramparser import AggregateParamParser, SearchParamParser
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.cache import AggregationCache

log = logging.getLogger(__name__)

class Api2Controller(BaseController):

    @jsonpify
    def aggregate(self):
        parser = AggregateParamParser(request.params)
        params, errors = parser.parse()

        if errors:
            response.status = 400
            return {'errors': errors}

        params['cuts'] = params.pop('cut')
        params['drilldowns'] = params.pop('drilldown')
        dataset = params.pop('dataset')
        require.dataset.read(dataset)

        try:
            cache = AggregationCache(dataset)
            result = cache.aggregate(**params)

            if cache.cache_enabled and 'cache_key' in result['summary']:
                if 'Pragma' in response.headers:
                    del response.headers['Pragma']
                response.cache_control = 'public; max-age: 84600'
                etag_cache(result['summary']['cache_key'])

        except (KeyError, ValueError) as ve:
            log.exception(ve)
            response.status = 400
            return {'errors': ['Invalid aggregation query: %r' % ve]}

        return result

    @jsonpify
    def search(self):
        parser = SearchParamParser(request.params)
        params, errors = parser.parse()

        if errors:
            response.status = 400
            return {'errors': errors}

        if params['filter']['dataset']:
            for dataset in params['filter'].get('dataset', []):
                  require.dataset.read(dataset)
        else:
            params['filter']['dataset'] = [ds.name for ds in model.Dataset.all_by_account(c.account)]

        b = Browser(**params)
        stats, facets, entries = b.execute()
        return {
            'stats': stats,
            'facets': facets,
            'results': list(entries)
        }
