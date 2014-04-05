import logging
import os

from pylons import config

from openspending.model import Dataset, meta as db
from openspending.tests.helpers import load_fixture

import migrate.versioning.api as migrate_api
from migrate.exceptions import DatabaseNotControlledError

log = logging.getLogger(__name__)


def drop():
    log.warn("Dropping database")
    db.metadata.reflect()
    db.metadata.drop_all()
    return 0


def drop_collections():
    # Kept for backwards compatibility
    return drop()


def drop_dataset(name):
    log.warn("Dropping dataset '%s'", name)
    dataset = db.session.query(Dataset).filter_by(name=name).first()
    if dataset is None:
        log.warn("Dataset does not exist: '%s'", name)
        return 1
    dataset.drop()
    db.session.delete(dataset)
    db.session.commit()
    return 0


def load_example(name):
    # TODO: separate the concepts of example/development data and test
    #       fixtures.
    load_fixture(name)
    return 0


def migrate():
    url = config.get('openspending.db.url')
    repo = config.get('openspending.migrate_dir',
                      os.path.join(os.path.dirname(config['__file__']),
                                   'migration'))

    try:
        migrate_api.upgrade(url, repo)
    except DatabaseNotControlledError:
        # Assume it's a new database, and try the migration again
        migrate_api.version_control(url, repo)
        migrate_api.upgrade(url, repo)

    diff = migrate_api.compare_model_to_db(url, repo, db.metadata)
    if diff:
        # Oh dear! The database we migrated to doesn't match openspending.model
        print diff
        return 1

    return 0


def modelmigrate():
    from openspending.validation.model.migration import migrate_model
    dataset = db.Table('dataset', db.metadata, autoload=True)
    rp = db.engine.execute(dataset.select())
    while True:
        ds = rp.fetchone()
        if ds is None:
            break
        print ds['name'], '...'
        model = migrate_model(ds['data'])
        version = model.get('dataset').get('schema_version')
        if 'dataset' in model:
            del model['dataset']
        q = dataset.update().where(dataset.c.id == ds['id'])
        q = q.values({'data': model, 'schema_version': version})
        db.engine.execute(q)
    return 0


def init():
    migrate()


def _init(args):
    return init()


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


def _modelmigrate(args):
    return modelmigrate()


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

    p = sp.add_parser('modelmigrate',
                      help='Run pending data model migrations')
    p.set_defaults(func=_modelmigrate)

    p = sp.add_parser('init',
                      help='Initialize the database')
    p.set_defaults(func=_init)
