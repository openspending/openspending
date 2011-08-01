import datetime

from openspending import mongo
from openspending.model import account
from openspending.test import DatabaseTestCase, helpers as h

def make_account():
    return {
        'name': 'Joe Bloggs',
        'label': 'Tester',
        'email': 'joe.bloggs@example.com'
    }

class TestAccount(DatabaseTestCase):

    def test_account_create_gives_api_key(self):
        _id = account.create(make_account())
        acc = account.get(_id)
        h.assert_equal(len(acc['api_key']), 36)

    def test_account_add_role(self):
        _id = account.create(make_account())
        account.add_role({'_id': _id}, 'admin')
        from_db = account.get(_id)
        h.assert_equal(from_db['roles'], ['admin'])