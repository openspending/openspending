import pkg_resources as _pkg_resources

from openspending.lib import json

from nose.tools import *
from mock import Mock, patch

class FixtureImportError(Exception):
    pass

def load_fixture(name):
    """
    Load fixture data into the database.
    """
    import os.path
    import subprocess

    from openspending.test import config

    def _load_collection_from_file(fname):
        if not fname.endswith('.json'):
            return # skip

        collection_name = fname[:-5]
        collection_fname = fixture_path(os.path.join(name, fname))

        # FIXME: shelling out here is really not ideal, but I can find no
        # way of achieving the same effect programmatically at the moment.

        db_name = config.get('openspending.mongodb.database')
        subprocess.check_output(['mongoimport',
                                 '--db', db_name,
                                 '--collection', collection_name,
                                 '--file', collection_fname])

    collection_filenames = fixture_listdir(name)

    for fname in collection_filenames:
        _load_collection_from_file(fname)

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
    from openspending import mongo
    mongo.drop_collections()

def clean_solr():
    '''Clean all entries from Solr.'''
    from openspending.lib.solr_util import get_connection
    solr = get_connection()
    solr.delete_query('*:*')
    solr.commit()

def clean_and_reindex_solr():
    '''Clean Solr and reindex all entries in the database.'''
    clean_solr()
    from openspending.lib.solr_util import build_index
    from openspending import model
    dataset_names = model.dataset.distinct('name')
    for name in dataset_names:
        build_index(name)

def skip_if_stubbed_solr():
    from openspending.lib.solr_util import get_connection, _Stub
    if type(get_connection()) == _Stub:
        skip("Not running test with stubbed Solr.")

def skip(*args, **kwargs):
    from nose.plugins.skip import SkipTest
    raise SkipTest(*args, **kwargs)

def mock_ckan(registry):
    '''
    Return a mock CKANClient that can be monkeypatched into the code while
    testing.
    '''
    class MockCKANClient(object):
        pass

    ckan = MockCKANClient()

    def mock_group_entity_get(name, *args, **kwargs):
        def in_group(p):
            return name in registry[p].get('groups', [])

        packages = filter(in_group, registry.keys())

        return {'packages': packages}

    def mock_package_entity_get(name, *args, **kwargs):
        return registry[name]

    ckan.group_entity_get = Mock(side_effect=mock_group_entity_get)
    ckan.package_entity_get = Mock(side_effect=mock_package_entity_get)

    return ckan