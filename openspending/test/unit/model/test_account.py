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

    def test_account_create(self):
        acc = make_account()
        acc['_id'] = 123
        _id = account.create(acc)
        h.assert_equal(_id, 123)
        from_db = mongo.db[account.collection].find_one({'_id': _id})
        h.assert_equal(from_db, acc)

    def test_account_find_one_by(self):
        mongo.db[account.collection].save({'name': 'foo', 'age': 23})
        mongo.db[account.collection].save({'name': 'bar', 'age': 50})
        found = account.find_one_by('name', 'foo')
        h.assert_equal(found['age'], 23)

    def test_account_find(self):
        mongo.db[account.collection].save({'name': 'foo', 'age': 23})
        mongo.db[account.collection].save({'name': 'bar', 'age': 50})
        mongo.db[account.collection].save({'name': 'baz', 'age': 50})
        found_names = [x['name'] for x in account.find({'age': 50})]
        h.assert_equal(found_names, ['bar', 'baz'])

    def test_account_create_gives_id(self):
        _id = account.create(make_account())
        acc = account.get(_id)
        h.assert_true(acc['_id'], "ID wasn't set on account object by 'create'!")

    def test_account_create_gives_api_key(self):
        _id = account.create(make_account())
        acc = account.get(_id)
        h.assert_equal(len(acc['api_key']), 36)

    def test_account_update(self):
        _id = account.create(make_account())
        account.update({'_id': _id}, {'$set': {'extrakey': 'foobar'}})
        from_db = account.get(_id)
        h.assert_equal(from_db['extrakey'], 'foobar')

    def test_account_add_role(self):
        _id = account.create(make_account())
        account.add_role({'_id': _id}, 'admin')
        from_db = account.get(_id)
        h.assert_equal(from_db['roles'], ['admin'])

    def test_account_add_flag(self):
        entry = {'_id': 'entryid'}
        _id = account.create(make_account())
        account.add_flag({'_id': _id}, entry, 'flagname')
        flags_from_db = account.get(_id)['flags']
        h.assert_equal(len(flags_from_db), 1)
        flag = flags_from_db[0]
        h.assert_equal(flag['type'], 'entry')
        h.assert_equal(flag['_id'], 'entryid')
        h.assert_equal(flag['flag'], 'flagname')
        delta = datetime.datetime.now() - flag['time']
        h.assert_less(delta.seconds, 10)
