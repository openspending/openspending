"""\
OpenSpending test module
========================

Run the OpenSpending test suite by running

    nosetests

in the root of the repository, while in an active virtualenv. See
doc/install.rst for more information.
"""

from pylons import config

from openspending import mongo
from .helpers import clean_all

__all__ = ['TestCase', 'DatabaseTestCase']

def setup_package():
    mongo.configure(config)

class TestCase(object):
    def setup(self):
        pass

    def teardown(self):
        pass

class DatabaseTestCase(TestCase):
    def teardown(self):
        clean_all()
        super(DatabaseTestCase, self).teardown()