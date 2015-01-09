import logging

from flask import request
from flask.ext.login import current_user
# from flask.ext.babel import gettext as _
from solr import SolrException

from openspending.auth import require
from openspending.model.dataset import Dataset
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.streaming import JSONStreamingResponse
from openspending.lib.streaming import CSVStreamingResponse
from openspending.lib.jsonexport import jsonify
from openspending.lib.csvexport import write_csv
from openspending.lib.paramparser import SearchParamParser
from openspending.lib.hypermedia import entry_apply_links
from openspending.lib.hypermedia import dataset_apply_links
from openspending.views.cache import etag_cache_keygen
from openspending.views.api_v2.new import blueprint


log = logging.getLogger(__name__)


@blueprint.route('/api/2/search')
def search():
    parser = SearchParamParser(request.args)
    params, errors = parser.parse()

    if errors:
        return jsonify({'errors': errors}, status=400)

    expand_facets = params.pop('expand_facet_dimensions')

    format = params.pop('format')
    if format == 'csv':
        params['stats'] = False
        params['facet_field'] = None

    datasets = params.pop('dataset', None)
    if datasets is None or not datasets:
        q = Dataset.all_by_account(current_user)
        if params.get('category'):
            q = q.filter_by(category=params.pop('category'))
        datasets = q.all()
        expand_facets = False

    if not datasets:
        return jsonify({'errors': ["No dataset available."]}, status=400)

    params['filter']['dataset'] = []
    for dataset in datasets:
        require.dataset.read(dataset)
        params['filter']['dataset'].append(dataset.name)

    etag_cache_keygen(parser.key(), max([d.updated_at for d in datasets]))

    if params['pagesize'] > parser.defaults['pagesize']:
        if format == 'csv':
            streamer = CSVStreamingResponse(
                datasets,
                params,
                pagesize=parser.defaults['pagesize']
            )
            return streamer.response()
        else:
            streamer = JSONStreamingResponse(
                datasets,
                params,
                pagesize=parser.defaults['pagesize'],
                expand_facets=util.expand_facets
                if expand_facets else None,
                callback=request.form.get('callback')
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
        return write_csv(entries, filename='entries.csv')

    if expand_facets and len(datasets) == 1:
        facets = solr_browser.get_expanded_facets(datasets[0])
    else:
        facets = solr_browser.get_facets()

    return jsonify({
        'stats': solr_browser.get_stats(),
        'facets': facets,
        'results': entries
    })
