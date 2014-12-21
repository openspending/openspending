import logging
import os

from openspending.core import db
from openspending.model import Dataset
from openspending.command.util import create_submanager
from openspending.command.util import CommandException

import migrate.versioning.api as migrate_api
from migrate.exceptions import DatabaseNotControlledError

log = logging.getLogger(__name__)

manager = create_submanager(description='Database operations')


@manager.command
def drop():
    """ Drop database """
    log.warn("Dropping database")
    db.metadata.reflect()
    db.metadata.drop_all()


@manager.command
def drop_dataset(name):
    """ Drop a dataset from the database """
    log.warn("Dropping dataset '%s'", name)
    dataset = db.session.query(Dataset).filter_by(name=name).first()
    if dataset is None:
        raise CommandException("Dataset does not exist: '%s'" % name)
    dataset.drop()
    db.session.delete(dataset)
    db.session.commit()


@manager.command
def migrate():
    """ Run pending data migrations """
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
        print diff
        raise CommandException("The database doesn't match the current model")


@manager.command
def modelmigrate():
    """ Run pending data model migrations """
    from openspending.validation.model.migration import migrate_model
    dataset = db.Table('dataset', db.metadata, autoload=True)
    rp = db.engine.execute(dataset.select())
    while True:
        ds = rp.fetchone()
        if ds is None:
            break
        log.info('Migrating %s...', ds['name'])
        model = migrate_model(ds['data'])
        version = model.get('dataset').get('schema_version')
        if 'dataset' in model:
            del model['dataset']
        q = dataset.update().where(dataset.c.id == ds['id'])
        q = q.values({'data': model, 'schema_version': version})
        db.engine.execute(q)


@manager.command
def init():
    """ Initialize the database """
    migrate()
