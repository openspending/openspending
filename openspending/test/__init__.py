"""\
OpenSpending test module
========================

Run the OpenSpending test suite by running

    nosetests

in the root of the repository, while in an active virtualenv. See
doc/install.rst for more information.
"""

import os
import sys

from paste.deploy import appconfig

from openspending import mongo
from helpers import clean_all

__all__ = ['TestCase', 'DatabaseTestCase']

here_dir = os.getcwd()
config = appconfig('config:test.ini', relative_to=here_dir)
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