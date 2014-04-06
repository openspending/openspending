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
        """
        Configure the database based on the provided configuration
        file, but be sure to overwrite the url so that it will use
        sqlite in memory, irrespective of what the user has set in
        test.ini. Construct the sqlalchemy engine with versioning
        and initialise everything.
        """

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
