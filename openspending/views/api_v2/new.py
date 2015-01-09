import logging
import urllib2
import json

from flask import request
from flask.ext.login import current_user
from colander import Invalid

from openspending import auth as can
from openspending.core import db
from openspending.auth import require
from openspending.model.dataset import Dataset
from openspending.model.source import Source
from openspending.lib.jsonexport import jsonify
from openspending.lib.paramparser import LoadingAPIParamParser
from openspending.lib.hypermedia import dataset_apply_links
from openspending.tasks import load_source, analyze_budget_data_package
from openspending.validation.model import validate_model
from openspending.views.api_v2.common import blueprint


log = logging.getLogger(__name__)


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
        return load_with_budget_data_package(
            params['budget_data_package'], params['private'])
    else:
        return load_with_model_and_csv(
            params['metadata'], params['csv_file'], params['private'])


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
