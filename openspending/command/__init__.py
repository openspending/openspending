# command.py
#
# The leaf classes in this module implement Paste Script commands; they
# are runnable with "paster thing", where thing is one of the commands
# listed in the openspending section of "paster help".
#
# They are registered in openspending's setup.py.
#
# See http://pythonpaste.org/script/developer.html for documentation of
# Paste Script.

import os
import sys
import argparse
import logging
import logging.config

from paste.deploy import appconfig
from openspending.ui.config.environment import load_environment

log = logging.getLogger(__name__.split('.')[0])

parser = argparse.ArgumentParser(description='Interface to common administrative tasks for OpenSpending.')
parser.add_argument('-v', '--verbose',
                    dest='verbose', action='append_const', const=1,
                    help='Increase the logging level')
parser.add_argument('-q', '--quiet',
                    dest='verbose', action='append_const', const=-1,
                    help='Decrease the logging level')
parser.add_argument('config', help='Paste configuration file')

subparsers = parser.add_subparsers(title='subcommands')

from . import db, solr, user, graph

for mod in (db, solr, user, graph):
    mod.configure_parser(subparsers)

try:
    from openspending.etl import command as etl_command
except ImportError:
    pass
else:
    etl_command.configure_parsers(subparsers)

def main():
    args = parser.parse_args()

    config_file = os.path.abspath(args.config)
    _configure_logging(config_file)
    _configure_pylons(config_file)

    args.verbose = 0 if args.verbose is None else sum(args.verbose)
    log.setLevel(max(10, log.getEffectiveLevel() - 10 * args.verbose))

    sys.exit(args.func(args))

def _configure_logging(config_file):
    logging.config.fileConfig(config_file,
                              dict(__file__=config_file,
                                   here=os.path.dirname(config_file)))

def _configure_pylons(config_file):
    conf = appconfig('config:%s' % os.path.basename(config_file),
                     relative_to=os.path.dirname(config_file))
    load_environment(conf.global_conf, conf.local_conf)

if __name__ == '__main__':
    main()
