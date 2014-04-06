from paste.script.appinstall import SetupCommand
from routes.util import URLGenerator
from pylons import url, config
from pylons.test import pylonsapp
from webtest import TestApp

from openspending.model import meta, init_model
from openspending.tests.helpers import clean_db

from sqlalchemy import engine_from_config
from migrate.versioning.util import construct_engine


class TestCase(object):

    def setup(self):
        pass

    def teardown(self):
        pass


class DatabaseTestCase(TestCase):

    def setup_database(self):
        '''
        Create a new, not scoped  global sqlalchemy session
        and rebind it to a new root transaction to which we can roll
        back. Otherwise :func:`adhocracy.model.init_model`
        will create as scoped session and invalidates
        the connection we need to begin a new root transaction.

        Return: The new root `connection`
        '''
        config['openspending.db.url'] = 'sqlite:///:memory:'
        engine = engine_from_config(config, 'openspending.db.')
        engine = construct_engine(engine)
        init_model(engine)

    def setup(self):
        self.setup_database()
        meta.metadata.create_all(meta.engine)

    def teardown(self):
        clean_db()
        super(DatabaseTestCase, self).teardown()


class ControllerTestCase(DatabaseTestCase):

    def __init__(self, *args, **kwargs):
        self.app = TestApp(pylonsapp)
        url._push_object(URLGenerator(config['routes.map'], {}))
        super(DatabaseTestCase, self).__init__(*args, **kwargs)
