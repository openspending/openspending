"""\
OpenSpending test module
========================

Run the OpenSpending test suite by running

    nosetests

in the root of the repository, while in an active virtualenv. See
doc/install.rst for more information.
"""

from pylons import config

from openspending.model import meta, init_model
from openspending.test.helpers import clean_all, clean_db

__all__ = ['TestCase', 'DatabaseTestCase']


def setup_package():
    '''
    Create a new, not scoped  global sqlalchemy session
    and rebind it to a new root transaction to which we can roll
    back. Otherwise :func:`adhocracy.model.init_model`
    will create as scoped session and invalidates
    the connection we need to begin a new root transaction.

    Return: The new root `connection`
    '''
    from sqlalchemy import engine_from_config
    from migrate.versioning.util import construct_engine
    config['openspending.db.url'] = 'sqlite:///:memory:'
    engine = engine_from_config(config, 'openspending.db.')
    engine = construct_engine(engine)
    init_model(engine)


class TestCase(object):

    def setup(self):
        pass

    def teardown(self):
        pass


class DatabaseTestCase(TestCase):

    def setup(self):
        setup_package()
        meta.metadata.create_all(meta.engine)

    def teardown(self):
        clean_db()
        super(DatabaseTestCase, self).teardown()
