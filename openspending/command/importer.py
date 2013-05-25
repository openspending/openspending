from __future__ import print_function

import argparse
import logging
import sys
import os
import urllib2
import urlparse

from openspending.lib import json

from openspending.model import Source, Dataset, Account, View
from openspending.model import meta as db

from openspending.importer import CSVImporter
from openspending.importer.analysis import analyze_csv

from openspending.command.archive import get_url_filename

from openspending.validation.model import validate_model
from openspending.validation.model import Invalid

log = logging.getLogger(__name__)

SHELL_USER = 'system'

import_parser = argparse.ArgumentParser(add_help=False)

import_parser.add_argument('-n', '--dry-run',
                           action="store_true", dest='dry_run', default=False,
                           help="Perform a dry run, don't load any data.")

import_parser.add_argument('--no-index', action="store_false", dest='build_indices',
                           default=True, help='Suppress Solr index build.')

import_parser.add_argument('--max-lines', action="store", dest='max_lines',
                           type=int, default=None, metavar='N',
                           help="Number of lines to import.")

import_parser.add_argument('--raise-on-error', action="store_true",
                           dest='raise_errors', default=False,
                           help='Get full traceback on first error.')

def shell_account():
    account = Account.by_name(SHELL_USER)
    if account is not None:
        return account
    account = Account()
    account.name = SHELL_USER
    db.session.add(account)
    return account

def _is_local_file(url):
    """
    Check to see if the provided url is a local file. Returns True if it is
    and False if it isn't. This method only checks if their is a scheme
    associated with the url or not (so file:location will be regarded as a url)
    """

    # Parse the url and check if scheme is '' (no scheme)
    parsed_result = urlparse.urlparse(url)
    return parsed_result.scheme == ''

def json_of_url(url):
    # Check if it's a local file
    if _is_local_file(url):
        # If it is we open it as a normal file
        return json.load(open(url, 'r'))
    else:
        # If it isn't we open the url as a file
        return json.load(urllib2.urlopen(url))

def create_view(dataset, view_config):
    """
    Create view for a provided dataset from a view provided as dict
    """

    # Check if it exists (if not we create it)
    existing = View.by_name(dataset, view_config['name'])
    if existing is None:
        # Create the view
        view = View()

        # Set saved configurations
        view.widget = view_config['widget']
        view.state = view_config['state']
        view.name = view_config['name']
        view.label = view_config['label']
        view.description = view_config['description']
        view.public = view_config['public']
        
        # Set the dataset as the current dataset
        view.dataset = dataset

        # Try and set the account provided but if it doesn't exist
        # revert to shell account
        view.account = Account.by_name(view_config['account'])
        if view.account is None:
            view.account = shell_account()

        # Commit view to database
        db.session.add(view)
        db.session.commit()

def get_model(model):
    """
    Get and validate the model. If the model doesn't validate we exit the
    program.
    """

    # Get and parse the model
    model = json_of_url(model)

    # Validate the model
    try:
        log.info("Validating model")
        model = validate_model(model)
    except Invalid, i:
        log.error("Errors occured during model validation:")
        for field, error in i.asdict().items():
            log.error("%s: %s", field, error)
        sys.exit(1)

    # Return the model
    return model

def get_or_create_dataset(model):
    """
    Based on a provided model we get the model (if it doesn't exist we
    create it).
    """

    # Get the dataset by the name provided in the model
    dataset = Dataset.by_name(model['dataset']['name'])

    # If the dataset wasn't found we create it
    if dataset is None:
        dataset = Dataset(model)
        db.session.add(dataset)
        db.session.commit()

    # Log information about the dataset and return it
    log.info("Dataset: %s", dataset.name)
    return dataset

def import_csv(dataset, url, args):
    """
    Import the csv data into the dataset
    """

    csv_data_url, source_url = url 
    source = Source(dataset, shell_account(), 
                    csv_data_url)
    # Analyse the csv data and add it to the source
    # If we don't analyse it we'll be left with a weird message
    source.analysis = analyze_csv(csv_data_url)
    # Check to see if the dataset already has this source
    for source_ in dataset.sources:
        if source_.url == csv_data_url:
            source = source_
            break
    db.session.add(source)
    db.session.commit()
    
    dataset.generate()
    importer = CSVImporter(source)
    importer.run(**vars(args))

    # Check if imported from the file system (source and data url differ)
    if csv_data_url != source_url:
        # If we did, then we must update the source url based on the
        # sources in the dataset model (so we need to fetch the source again
        # or else we'll add a new one)
        source = Source.by_id(source.id)
        source.url = source_url
        db.session.commit()

def import_views(dataset, views_url):
    """
    Import views into the provided dataset which are defined in a json object
    located at the views_url
    """

    # Load the json and loop over its 'visualisations' property
    for view in json_of_url(views_url)['visualisations']:
        create_view(dataset, view)

def map_source_urls(model, urls):
    """
    Go through the source urls of the dataset model and map them to the
    files or urls. Returns a dict where the key is the url and the value
    is how it should be represented in the dataset.
    """

    # Create map from file to model sources
    source_files = {get_url_filename(s):s 
                    for s in model['dataset'].get('sources', [])}

    # Return a map for the representation of csv urls
    return {u:source_files.get(os.path.basename(u), u) for u in urls}

def _csvimport(args):
    """
    Parse the arguments and pass them to the processing functions
    """
    # Get the model
    model = get_model(args.model)

    # Get the source map (data urls to models)
    source_map = map_source_urls(model, args.dataset_urls)

    # Get the dataset for the model
    dataset = get_or_create_dataset(model)

    # For every url in mapped dataset_urls (arguments) we import it
    for urlmap in source_map.iteritems():
        import_csv(dataset, urlmap, args)

    # Import visualisations if there are any
    if args.views:
        import_views(dataset, args.views)

def configure_parser(subparser):
    p = subparser.add_parser('csvimport',
                             help='Load a CSV dataset',
                             description='You must specify --model.',
                             parents=[import_parser])
    # Add the model argument which is required
    p.add_argument('--model', action="store", dest='model',
                   default=None, metavar='url', required=True,
                   help="URL of JSON format model (metadata and mapping).")
    # Allow user to define url or file with visualisations
    p.add_argument('--visualisations', action="store", dest="views",
                   default=None, metavar='url/file',
                   help="URL/file of JSON format visualisations.")
    # Load multiple sources via the dataset_urls (all remaining arguments)
    p.add_argument('dataset_urls', nargs=argparse.REMAINDER, 
                   help="Dataset file URL")
    p.set_defaults(func=_csvimport)

