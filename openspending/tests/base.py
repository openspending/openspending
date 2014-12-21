from flask.ext.testing import TestCase as FlaskTestCase

from openspending.core import create_app
from openspending.tests.helpers import clean_db, init_db


class TestCase(FlaskTestCase):

    def create_app(self):
        app = create_app(**{
            'DEBUG': True,
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'CELERY_ALWAYS_EAGER': True
        })
        #init_db(app)
        return app

    def setUp(self):
        init_db(self.app)

    def tearDown(self):
        clean_db(self.app)


class DatabaseTestCase(TestCase):
    pass


#class ControllerTestCase(DatabaseTestCase):
#
#    def __init__(self, *args, **kwargs):
#        self.app = TestApp(pylonsapp)
#        url._push_object(URLGenerator(config['routes.map'], {}))
#        super(DatabaseTestCase, self).__init__(*args, **kwargs)
