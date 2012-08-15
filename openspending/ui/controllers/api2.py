import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import etag_cache

from openspending import model
from openspending import auth as can
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.solr_util import SolrException
from openspending.lib.jsonexport import jsonpify, to_jsonp
from openspending.lib.csvexport import write_csv
from openspending.lib.paramparser import AggregateParamParser, SearchParamParser
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.base import etag_cache_keygen
from openspending.ui.lib.cache import AggregationCache
from openspending.ui.lib.hypermedia import entry_apply_links, drilldowns_apply_links

log = logging.getLogger(__name__)

class Api2Controller(BaseController):

    def aggregate(self):
        parser = AggregateParamParser(request.params)
        params, errors = parser.parse()

        if errors:
            response.status = 400
            return {'errors': errors}

        params['cuts'] = params.pop('cut')
        params['drilldowns'] = params.pop('drilldown')
        dataset = params.pop('dataset')
        format = params.pop('format')
        require.dataset.read(dataset)

        try:
            cache = AggregationCache(dataset)
            result = cache.aggregate(**params)
            if 'drilldown' in result:
                result['drilldown'] = drilldowns_apply_links(dataset.name,
                    result['drilldown'])

            response.last_modified = dataset.updated_at
            if cache.cache_enabled and 'cache_key' in result['summary']:
                etag_cache(result['summary']['cache_key'])

        except (KeyError, ValueError) as ve:
            log.exception(ve)
            response.status = 400
            return {'errors': ['Invalid aggregation query: %r' % ve]}

        if format == 'csv':
            return write_csv(result['drilldown'], response,
                filename=dataset.name + '.csv')
        return to_jsonp(result)

    @jsonpify
    def search(self):
        parser = SearchParamParser(request.params)
        params, errors = parser.parse()

        if errors:
            response.status = 400
            return {'errors': errors}

        expand_facets = params.pop('expand_facet_dimensions')

        datasets = params.pop('dataset', None)
        if datasets is None or not len(datasets):
            q = model.Dataset.all_by_account(c.account)
            if params.get('category'):
                q = q.filter_by(category=params.pop('category'))
            datasets = q.all()
            expand_facets = False

        params['filter']['dataset'] = []
        for dataset in datasets:
            require.dataset.read(dataset)
            params['filter']['dataset'].append(dataset.name)

        if not len(datasets):
            return {'errors': [_("No dataset available.")]}
        
        response.last_modified = max([d.updated_at for d in datasets])
        etag_cache_keygen(parser.key(), response.last_modified)

        b = Browser(**params)
        try:
            stats, facets, entries = b.execute()
        except SolrException, e:
            return {'errors': [unicode(e)]}

        _entries = []
        for dataset, entry in entries:
            if not can.dataset.read(dataset):
                continue
            entry = entry_apply_links(dataset.name, entry)
            entry['dataset'] = { 'name': dataset.name,
                                 'label': dataset.label }
            _entries.append(entry)

        if expand_facets and len(datasets) == 1:
            _expand_facets(facets, datasets[0])

        return {
            'stats': stats,
            'facets': facets,
            'results': _entries
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
