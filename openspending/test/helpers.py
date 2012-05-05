# Shut up nose DeprecationWarnings
import warnings
warnings.filterwarnings('ignore', 'The compiler package is deprecated and removed in Python 3.x.')

from nose.tools import *
from nose.plugins.skip import SkipTest
from mock import Mock, patch, MagicMock

from datetime import datetime
import os as _os
import csv
import json

from openspending.model import Dataset, meta as db
from openspending.lib import solr_util as _solr

TEST_ROOT = _os.path.dirname(__file__)

def load_fixture(name, manager=None):
    """
    Load fixture data into the database.
    """
    from openspending.validation.data import convert_types
    fh = fixture_file('%s.js' % name)
    data = json.load(fh)
    fh.close()
    dataset = Dataset(data)
    dataset.updated_at = datetime.utcnow()
    if manager is not None:
        dataset.managers.append(manager)
    db.session.add(dataset)
    db.session.commit()
    dataset.generate()
    fh = fixture_file('%s.csv' % name)
    reader = csv.DictReader(fh)
    for row in reader:
        entry = convert_types(data['mapping'], row)
        dataset.load(entry)
    fh.close()
    dataset.commit()
    return dataset

def fixture_file(name):
    """Return a file-like object pointing to a named fixture."""
    return open(fixture_path(name))

def model_fixture(name):
    model_fp = fixture_file('model/' + name + '.json')
    model = json.load(model_fp)
    model_fp.close()
    return model

def fixture_path(name):
    """
    Return the full path to a named fixture.

    Use fixture_file rather than this method wherever possible.
    """
    return _os.path.join(TEST_ROOT, 'fixtures', name)

def clean_all():
    clean_db()
    clean_solr()

def make_account(name='test', fullname='Test User',
                 email='test@example.com'):
    from openspending.model import Account
    account = Account()
    account.name = name
    account.fullname = fullname
    account.email = email
    db.session.add(account)
    db.session.commit()
    return account

def clean_db():
    db.session.rollback()
    db.metadata.drop_all()

def clean_solr():
    '''Clean all entries from Solr.'''
    s = _solr.get_connection()
    s.delete_query('*:*')
    s.commit()

def clean_and_reindex_solr():
    '''Clean Solr and reindex all entries in the database.'''
    clean_solr()
    for dataset in db.session.query(Dataset):
        _solr.build_index(dataset.name)

def skip(*args, **kwargs):
    raise SkipTest(*args, **kwargs)


