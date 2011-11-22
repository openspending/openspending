from __future__ import print_function

import argparse
import logging
import sys
import urllib2

from openspending.lib import json

from openspending.importer import util
from openspending.importer import CSVImporter

log = logging.getLogger(__name__)

import_parser = argparse.ArgumentParser(add_help=False)

import_parser.add_argument('-n', '--dry-run',
                           action="store_true", dest='dry_run', default=False,
                           help="Perform a dry run, don't load any data.")

import_parser.add_argument('--no-index', action="store_false", dest='build_indices',
                           default=True, help='Suppress Solr index build.')

import_parser.add_argument('--max-errors', action="store", dest='max_errors',
                           type=int, default=None, metavar='N',
                           help="Maximum number of import errors to tolerate before giving up.")

import_parser.add_argument('--max-lines', action="store", dest='max_lines',
                           type=int, default=None, metavar='N',
                           help="Number of lines to import.")

import_parser.add_argument('--raise-on-error', action="store_true",
                           dest='raise_errors', default=False,
                           help='Get full traceback on first error.')

def csvimport(csv_data_url, args):

    def json_of_url(url):
        return json.load(urllib2.urlopen(url))

    if args.model:
        model = json_of_url(args.model)
    else:
        print("You must provide --model!",
              file=sys.stderr)
        return 1

    csv = util.urlopen_lines(csv_data_url)
    importer = CSVImporter(csv, model, csv_data_url)

    importer.run(**vars(args))
    return 0

def _csvimport(args):
    return csvimport(args.dataset_url, args)

def configure_parser(subparser):
    p = subparser.add_parser('csvimport',
                             help='Load a CSV dataset',
                             description='You must specify one of --model OR (--mapping AND --metadata).',
                             parents=[import_parser])
    p.add_argument('--model', action="store", dest='model',
                   default=None, metavar='url',
                   help="URL of JSON format model (metadata and mapping).")
    p.add_argument('dataset_url', help="Dataset file URL")
    p.set_defaults(func=_csvimport)

