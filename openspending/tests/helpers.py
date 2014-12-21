from openspending.validation.data import convert_types
from openspending.model.dataset import Dataset
from openspending.core import app, db
from openspending.lib import solr_util as solr

from datetime import datetime
import os.path
import json
import csv


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
    # Get the directory of this file (helpers is placed in the test directory)
    test_directory = os.path.dirname(__file__)
    # Fixture is a directory in the test directory
    return os.path.join(test_directory, 'fixtures', name)


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


def make_account(name='test', fullname='Test User',
                 email='test@example.com', twitter='testuser',
                 admin=False):
    from openspending.model.account import Account

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


def init_db():
    app.config['TESTING'] = True
    #app.config['CELERY_ALWAYS_EAGER'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.create_all()


def clean_db():
    db.session.rollback()
    db.drop_all()


def clean_solr():
    '''Clean all entries from Solr.'''
    s = solr.get_connection()
    s.delete_query('*:*')
    s.commit()


def clean_and_reindex_solr():
    '''Clean Solr and reindex all entries in the database.'''
    clean_solr()
    for dataset in db.session.query(Dataset):
        solr.build_index(dataset.name)
