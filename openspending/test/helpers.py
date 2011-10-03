from nose.tools import *
from nose.plugins.skip import SkipTest
from mock import Mock, patch, MagicMock

import os as _os

from openspending import model as _model
from openspending.lib import solr_util as _solr

TEST_ROOT = _os.path.dirname(__file__)

def load_fixture(name):
    """
    Load fixture data into the database.
    """
    _pymongodump.restore(_mongo.db, fixture_path('%s.pickle' % name), drop=False)

def fixture_file(name):
    """Return a file-like object pointing to a named fixture."""
    return open(fixture_path(name))

def fixture_path(name):
    """
    Return the full path to a named fixture.

    Use fixture_file rather than this method wherever possible.
    """
    return _os.path.join(TEST_ROOT, 'fixtures', name)

def clean_all():
    clean_db()
    clean_solr()

def clean_db():
    _model.meta.session.rollback()
    _model.meta.metadata.drop_all()

def clean_solr():
    '''Clean all entries from Solr.'''
    s = _solr.get_connection()
    s.delete_query('*:*')
    s.commit()

def clean_and_reindex_solr():
    '''Clean Solr and reindex all entries in the database.'''
    clean_solr()
    dataset_names = _model.dataset.distinct('name')
    for name in dataset_names:
        _solr.build_index(name)

def skip_if_stubbed_solr():
    if type(_solr.get_connection()) == _solr._Stub:
        skip("Not running test with stubbed Solr.")

def skip(*args, **kwargs):
    raise SkipTest(*args, **kwargs)


