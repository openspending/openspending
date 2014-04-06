# Silence nose DeprecationWarnings
import warnings
warnings.filterwarnings(
    'ignore',
    'The compiler package is deprecated and removed in Python 3.x.')

from datetime import datetime
import os as _os
import csv
import json

from openspending.validation.data import convert_types
from openspending.model import Dataset, meta as db
from openspending.lib import solr_util as _solr
import csv


TEST_ROOT = _os.path.dirname(__file__)


def fixture_file(name):
    """Return a file-like object pointing to a named fixture."""
    return open(fixture_path(name))


def model_fixture(name):
    model_fp = fixture_file('model/' + name + '.json')
    model = json.load(model_fp)
    model_fp.close()
    return model


def data_fixture(name):
    return fixture_file('data/' + name + '.csv')


def fixture_path(name):
    """
    Return the full path to a named fixture.

    Use fixture_file rather than this method wherever possible.
    """
    return _os.path.join(TEST_ROOT, 'fixtures', name)


def load_fixture(name, manager=None):
    """
    Load fixture data into the database.
    """
    model = model_fixture(name)
    dataset = Dataset(model)
    dataset.updated_at = datetime.utcnow()
    if manager is not None:
        dataset.managers.append(manager)
    db.session.add(dataset)
    db.session.commit()
    dataset.generate()
    data = data_fixture(name)
    reader = csv.DictReader(data)
    for row in reader:
        entry = convert_types(model['mapping'], row)
        dataset.load(entry)
    data.close()
    dataset.commit()
    return dataset


def load_dataset(dataset):
    simple_model = model_fixture('simple')
    data = data_fixture('simple')
    reader = csv.DictReader(data)
    for row in reader:
        row = convert_types(simple_model['mapping'], row)
        dataset.load(row)
    data.close()


def clean_all():
    clean_db()
    clean_solr()


def make_account(name='test', fullname='Test User',
                 email='test@example.com', twitter='testuser',
                 admin=False):
    from openspending.model import Account

    # First see if the account already exists and if so, return it
    account = Account.by_name(name)
    if account:
        return account

    # Account didn't exist so we create it and return it
    account = Account()
    account.name = name
    account.fullname = fullname
    account.email = email
    account.twitter_handle = twitter
    account.admin = admin
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
