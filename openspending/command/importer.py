from __future__ import print_function

import argparse
import logging
import sys
import urllib2
import urlparse

from openspending.lib import json

from openspending.model import Source, Dataset, Account, View
from openspending.model import meta as db
from openspending.importer import CSVImporter
from openspending.importer.analysis import analyze_csv
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

def create_view(dataset, view):
    """
    Create view for a provided dataset from a view provided as dict
    """

    # Check if it exists (if not we create it)
    existing = View.by_name(dataset, view['name'])
    if existing is None:
        # Create the view
        view = View()

        # Set saved configurations
        view.widget = view['widget']
        view.state = view['state']
        view.name = view['name']
        view.label = view['label']
        view.description = view['description']
        view.public = view['public']
        
        # Set the dataset as the current dataset
        view.dataset = dataset

        # Try and set the account provided but if it doesn't exist
        # revert to shell account
        view.account = Account.by_name(view['account'])
        if view.account is None:
            view.account = shell_account()

        # Commit view to database
        db.session.add(view)
        db.session.commit()

def csvimport(csv_data_url, args):

    def json_of_url(url):
        # Check if it's an internet url (by checking scheme)
        parsed_result = urlparse.urlparse(url)
        if parsed_result.scheme:
            return json.load(urllib2.urlopen(url))
        # If it doesn't have any scheme it's probably a file
        # if not we'll just forward the raised error
        else:
            return json.load(open(url, 'r'))
        
    if not args.model:
        print("You must provide --model!",
              file=sys.stderr)
        sys.exit(1)

    model = json_of_url(args.model)
    try:
        log.info("Validating model")
        model = validate_model(model)
    except Invalid, i:
        log.error("Errors occured during model validation:")
        for field, error in i.asdict().items():
            log.error("%s: %s", field, error)
        sys.exit(1)

    dataset = Dataset.by_name(model['dataset']['name'])
    if dataset is None:
        dataset = Dataset(model)
        db.session.add(dataset)
    log.info("Dataset: %s", dataset.name)

    source = Source(dataset, shell_account(), 
                    csv_data_url)
    # Analyse the csv data and add it to the source
    # If we don't analyse it we'll be left with a weird message
    source.analysis = analyze_csv(csv_data_url)
    for source_ in dataset.sources:
        if source_.url == csv_data_url:
            source = source_
            break
    db.session.add(source)
    db.session.commit()
    
    dataset.generate()
    importer = CSVImporter(source)
    importer.run(**vars(args))

    # Import the views the the user has provided a visualisation file/url
    if args.views:
        for view in json_of_url(args.views)['visualisations']:
            create_view(dataset, view)

def _csvimport(args):
    # For every url in dataset_urls (arguments) we import it
    for url in args.dataset_urls:
        csvimport(url, args)

def configure_parser(subparser):
    p = subparser.add_parser('csvimport',
                             help='Load a CSV dataset',
                             description='You must specify --model.',
                             parents=[import_parser])
    p.add_argument('--model', action="store", dest='model',
                   default=None, metavar='url',
                   help="URL of JSON format model (metadata and mapping).")
    # Allow user to define url or file with visualisations
    p.add_argument('--visualisations', action="store", dest="views",
                   default=None, metavar='url/file',
                   help="URL/file of JSON format visualisations.")
    # Load multiple sources via the dataset_urls (all remaining arguments)
    p.add_argument('dataset_urls', nargs=argparse.REMAINDER, 
                   help="Dataset file URL")
    p.set_defaults(func=_csvimport)

