import logging
import urllib2
import json

from flask import Blueprint, request
from flask.ext.login import current_user
# from flask.ext.babel import gettext as _
from colander import Invalid
from solr import SolrException

from openspending import auth as can
from openspending.core import db
from openspending.auth import require
from openspending.model.dataset import Dataset
from openspending.model.source import Source
from openspending.lib import util
from openspending.lib.browser import Browser
from openspending.lib.streaming import JSONStreamingResponse
from openspending.lib.streaming import CSVStreamingResponse
from openspending.lib.jsonexport import jsonify
from openspending.lib.csvexport import write_csv
from openspending.lib.paramparser import AggregateParamParser
from openspending.lib.paramparser import SearchParamParser
from openspending.lib.paramparser import LoadingAPIParamParser
from openspending.lib.cache import AggregationCache
from openspending.lib.hypermedia import entry_apply_links
from openspending.lib.hypermedia import drilldowns_apply_links
from openspending.lib.hypermedia import dataset_apply_links
from openspending.tasks import load_source, analyze_budget_data_package
from openspending.validation.model import validate_model
from openspending.views.cache import etag_cache_keygen


log = logging.getLogger(__name__)
blueprint = Blueprint('api', __name__)


@blueprint.route('/api/2/aggregate')
def aggregate():
    """
    Aggregation of a dataset based on URL parameters. It serves the
    aggregation from a cache if possible, and if not it computes it (it's
    performed in the aggregation cache for some reason).
    """

    # Parse the aggregation parameters to get them into the right format
    parser = AggregateParamParser(request.args)
    params, errors = parser.parse()

    # If there were parsing errors we return them with status code 400
    # as jsonp, irrespective of what format was asked for.
    if errors:
        return jsonify({'errors': errors}, status=400)

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
        #response.last_modified = dataset.updated_at
        if 'cache_key' in result['summary']:
            etag_cache_keygen(result['summary']['cache_key'])

    except (KeyError, ValueError) as ve:
        # We log possible errors and return them with status code 400
        log.exception(ve)
        return jsonify({'errors': [unicode(ve)]}, status=400)

    # If the requested format is csv we write the drilldown results into
    # a csv file and return it, if not we return a jsonp result (default)
    if format == 'csv':
        return write_csv(result['drilldown'], filename=dataset.name + '.csv')
    return jsonify(result)


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
        return {'errors': ["No dataset available."]}

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


@blueprint.route('/api/2/new', methods=['POST'])
def create():
    """ Adds a new dataset dynamically through a POST request. """
    require.account.logged_in()

    # Parse the loading api parameters to get them into the right format
    parser = LoadingAPIParamParser(request.form)
    params, errors = parser.parse()

    if errors:
        return jsonify({'errors': errors}, status=400)

    # Precedence of budget data package over other methods
    if 'budget_data_package' in params:
        output = load_with_budget_data_package(
            params['budget_data_package'], params['private'])
    else:
        output = load_with_model_and_csv(
            params['metadata'], params['csv_file'], params['private'])

    return output


def load_with_budget_data_package(bdp_url, private):
    """ Analyze and load data using a budget data package """
    analyze_budget_data_package.delay(bdp_url, current_user, private)


def load_with_model_and_csv(metadata, csv_file, private):
    """ Load a dataset using a metadata model file and a csv file """

    if metadata is None:
        return jsonify({'errors': 'metadata is missing'}, status=400)

    if csv_file is None:
        return jsonify({'errors': 'csv_file is missing'}, status=400)
        
    # We proceed with the dataset
    try:
        model = json.load(urllib2.urlopen(metadata))
    except:
        return jsonify({'errors': 'JSON model could not be parsed'}, status=400)
    try:
        log.info("Validating model")
        model = validate_model(model)
    except Invalid as i:
        log.error("Errors occured during model validation:")
        for field, error in i.asdict().items():
            log.error("%s: %s", field, error)
        return jsonify({'errors': 'Model is not well formed'}, status=400)
    dataset = Dataset.by_name(model['dataset']['name'])
    if dataset is None:
        dataset = Dataset(model)
        require.dataset.create()
        dataset.managers.append(current_user)
        dataset.private = private
        db.session.add(dataset)
    else:
        require.dataset.update(dataset)

    log.info("Dataset: %s", dataset.name)
    source = Source(dataset=dataset, creator=current_user,
                    url=csv_file)

    log.info(source)
    for source_ in dataset.sources:
        if source_.url == csv_file:
            source = source_
            break
    db.session.add(source)
    db.session.commit()

    # Send loading of source into celery queue
    load_source.delay(source.id)
    return jsonify(dataset_apply_links(dataset.as_dict()))


@blueprint.route('/api/2/permissions')
def permissions():
    """
    Check a user's permissions for a given dataset. This could also be
    done via request to the user, but since we're not really doing a
    RESTful service we do this via the api instead.
    """
    if 'dataset' not in request.args:
        return jsonify({'error': 'Parameter dataset missing'}, status=400)

    # Get the dataset we want to check permissions for
    dataset = Dataset.by_name(request.args['dataset'])

    # Return permissions
    return jsonify({
        'create': can.dataset.create() and dataset is None,
        'read': False if dataset is None else can.dataset.read(dataset),
        'update': False if dataset is None else can.dataset.update(dataset),
        'delete': False if dataset is None else can.dataset.delete(dataset)
    })
