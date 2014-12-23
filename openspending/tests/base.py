import tempfile

from flask.ext.testing import TestCase as FlaskTestCase

from openspending.core import create_app
from openspending.tests.helpers import clean_db, init_db


class TestCase(FlaskTestCase):

    def create_app(self):
        app = create_app(**{
            'DEBUG': True,
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'CELERY_ALWAYS_EAGER': True,
            'UPLOADS_DEFAULT_DEST': tempfile.mkdtemp()
        })
        #init_db(app)
        return app

    def setUp(self):
        init_db(self.app)

    def tearDown(self):
        clean_db(self.app)


class DatabaseTestCase(TestCase):
    pass


class ControllerTestCase(DatabaseTestCase):
    pass
