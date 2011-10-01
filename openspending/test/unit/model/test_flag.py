import datetime

from openspending import model
from ... import DatabaseTestCase, helpers as h

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
        model.dataset.create({'_id': 'datasetid', 'name': 'datasetname'})
        dataset = model.dataset.get('datasetid')
        entry = model.entry.create({'_id': 'entryid'}, dataset)
        account = model.account.create({'_id': 'accountid'})

        model.flag.inc_flag(entry, 'interesting', account)

        entry = model.entry.get('entryid') # sync with db
        f = entry['flags']['interesting']
        h.assert_equal(len(f['flaggings']), 1)
        flag = f['flaggings'][0]
        h.assert_equal(flag['account'], 'accountid')
        delta = datetime.datetime.now() - flag['time']
        h.assert_less(delta.seconds, 10)

    def test_inc_flag_on_account(self):
        dataset = model.dataset.create({'_id': 'datasetid',
                                        'name': 'datasetname'})
        entry = model.entry.create({'_id': 'entryid'}, dataset)
        account = model.account.create({'_id': 'accountid'})

        model.flag.inc_flag(entry, 'interesting', account)

        account = model.account.get('accountid')
        f_all = account['flags']
        h.assert_equal(len(f_all), 1)
        f = f_all[0]
        h.assert_equal(f['type'], 'entry')
        h.assert_equal(f['_id'], 'entryid')
        h.assert_equal(f['flag'], 'interesting')
        delta = datetime.datetime.now() - f['time']
        h.assert_less(delta.seconds, 10)
