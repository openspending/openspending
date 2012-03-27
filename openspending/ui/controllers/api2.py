import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import etag_cache

from openspending import model
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.jsonexport import jsonpify
from openspending.lib.paramparser import AggregateParamParser, SearchParamParser
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.cache import AggregationCache
from openspending.ui.lib.hypermedia import entry_apply_links, drilldowns_apply_links

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
            if 'drilldown' in result:
                result['drilldown'] = drilldowns_apply_links(dataset.name,
                    result['drilldown'])

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

        expand_facets = params.pop('expand_facet_dimensions')

        datasets = params.pop('dataset', None)
        if datasets is None:
            datasets = model.Dataset.all_by_account(c.account)
            expand_facets = False

        for dataset in datasets:
            require.dataset.read(dataset)

        b = Browser(**params)
        stats, facets, entries = b.execute()
        entries = [entry_apply_links(d.name, e) for d, e in entries]

        if expand_facets and len(datasets) == 1:
            _expand_facets(facets, datasets[0])

        return {
            'stats': stats,
            'facets': facets,
            'results': entries
        }

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
