import datetime

from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

class TestFlag(DatabaseTestCase):

    def test_get_flag_for_entry_noflags(self):
        entry = {'_id': 'entryid'}
        from_db = model.flag.get_flag_for_entry(entry, 'interesting')
        h.assert_equal(from_db['count'], 0)
        h.assert_equal(len(from_db['flaggings']), 0)

    def test_get_flag_for_entry_flags_noflag(self):
        entry = {'_id': 'entryid', 'flags': {}}
        from_db = model.flag.get_flag_for_entry(entry, 'interesting')
        h.assert_equal(from_db['count'], 0)
        h.assert_equal(len(from_db['flaggings']), 0)

    def test_get_flag_for_entry(self):
        f = {'count': 1, 'flaggings': [{}]}
        entry = {'_id': 'entryid', 'flags': {'interesting': f}}
        from_db = model.flag.get_flag_for_entry(entry, 'interesting')
        h.assert_equal(from_db['count'], 1)
        h.assert_equal(len(from_db['flaggings']), 1)

    @h.raises(KeyError)
    def test_get_unknown_flag(self):
        entry = {'_id': 'entryid'}
        model.flag.get_flag_for_entry(entry, 'somethingelse')

    def test_inc_flag_on_entry(self):
        dataset = model.Dataset({'_id': 'datasetid', 'name': 'datasetname'})
        dataset.save()
        entry = {'_id': 'entryid'}
        account = {'_id': 'accountid'}

        _id = model.entry.create(entry, dataset)
        model.account.create(account)

        model.flag.inc_flag(entry, 'interesting', account)

        f = model.entry.get(_id)['flags']['interesting']

        h.assert_equal(len(f['flaggings']), 1)
        flag = f['flaggings'][0]
        h.assert_equal(flag['account'], 'accountid')
        delta = datetime.datetime.now() - flag['time']
        h.assert_less(delta.seconds, 10)

    def test_inc_flag_on_account(self):
        dataset = model.Dataset({'_id': 'datasetid', 'name': 'datasetname'})
        dataset.save()
        entry = {'_id': 'entryid'}
        account = {'_id': 'accountid'}

        model.entry.create(entry, dataset)
        _id = model.account.create(account)

        model.flag.inc_flag(entry, 'interesting', account)

        from_db = model.account.get(_id)['flags']
        h.assert_equal(len(from_db), 1)
        f = from_db[0]
        h.assert_equal(f['type'], 'entry')
        h.assert_equal(f['_id'], 'entryid')
        h.assert_equal(f['flag'], 'interesting')
        delta = datetime.datetime.now() - f['time']
        h.assert_less(delta.seconds, 10)
