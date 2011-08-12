from nose.tools import *
from nose.plugins.skip import SkipTest
from mock import Mock, patch, MagicMock

import pkg_resources as _pkg_resources

from .. import model as _model
from .. import mongo as _mongo
from ..lib import solr_util as _solr
from . import pymongodump as _pymongodump

class FixtureImportError(Exception):
    pass

def load_fixture(name):
    """
    Load fixture data into the database.
    """
    _pymongodump.restore(_mongo.db, fixture_path('%s.pickle' % name), drop=False)

def _fixture_relpath(name):
    return 'fixtures/%s' % name

def fixture_file(name):
    """Return a file-like object pointing to a named fixture."""
    return _pkg_resources.resource_stream(__name__, _fixture_relpath(name))

def fixture_path(name):
    """
    Return the full path to a named fixture.

    Use fixture_file rather than this method wherever possible.
    """
    return _pkg_resources.resource_filename(__name__, _fixture_relpath(name))

def fixture_listdir(name):
    """Return a directory listing for the named fixture."""
    return _pkg_resources.resource_listdir(__name__, _fixture_relpath(name))

def clean_all():
    clean_db()
    clean_solr()

def clean_db():
    _mongo.drop_collections()

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


