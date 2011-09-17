import logging
import os

from pylons import config

from openspending import mongo
from openspending import migration
from openspending.test.helpers import load_fixture

log = logging.getLogger(__name__)

def drop():
    log.warn("Dropping database")
    mongo.drop_db()
    return 0

def drop_collections():
    log.warn("Dropping collections from database")
    mongo.drop_collections()
    return 0

def drop_dataset(name):
    log.warn("Dropping dataset '%s'", name)

    log.info("Removing entries for dataset %s", name)
    mongo.db.entry.remove({'dataset.name': name})

    log.info("Removing dimensions for dataset %s", name)
    mongo.db.dimension.remove({'dataset': name})

    log.info("Removing distincts for dataset %s", name)
    mongo.db['distincts__%s' % name].drop()

    log.info("Removing cubes for dataset %s", name)
    cubes = filter(lambda x: x.startswith('cubes.%s.' % name),
                   mongo.db.collection_names())
    for c in cubes:
        mongo.db[c].drop()

    log.info("Removing dataset object for dataset %s", name)
    mongo.db.dataset.remove({'name': name})
    return 0

def load_example(name):
    # TODO: separate the concepts of example/development data and test
    #       fixtures.
    load_fixture(name)
    return 0

def migrate():
    default = os.path.join(os.path.dirname(config['__file__']), 'migrate')
    migrate_dir = config.get('openspending.migrate_dir', default)

    migration.configure(dirname=migrate_dir)
    migration.up()
    return

def _drop(args):
    return drop()

def _drop_collections(args):
    return drop_collections()

def _drop_dataset(args):
    return drop_dataset(args.name)

def _load_example(args):
    return load_example(args.name)

def _migrate(args):
    return migrate()

def configure_parser(subparsers):
    parser = subparsers.add_parser('db', help='Database operations')
    sp = parser.add_subparsers(title='subcommands')

    p = sp.add_parser('drop', help='Drop database')
    p.set_defaults(func=_drop)

    p = sp.add_parser('dropcollections',
                      help='Drop collections within database')
    p.set_defaults(func=_drop_collections)

    p = sp.add_parser('dropdataset',
                      help='Drop a dataset from the database')
    p.add_argument('name')
    p.set_defaults(func=_drop_dataset)

    p = sp.add_parser('loadexample',
                      help='Load an example dataset into the database')
    p.add_argument('name')
    p.set_defaults(func=_load_example)

    p = sp.add_parser('migrate',
                      help='Run pending data migrations')
    p.set_defaults(func=_migrate)