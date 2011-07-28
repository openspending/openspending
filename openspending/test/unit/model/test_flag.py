import datetime

from openspending.model import account, Entry, flag
from openspending.test import DatabaseTestCase, helpers as h

class TestFlag(DatabaseTestCase):

    def test_get_flag_for_entry_noflags(self):
        ent = {'_id': 'entryid'}
        from_db = flag.get_flag_for_entry(ent, 'interesting')
        h.assert_equal(from_db['count'], 0)
        h.assert_equal(len(from_db['flaggings']), 0)

    def test_get_flag_for_entry_flags_noflag(self):
        ent = {'_id': 'entryid', 'flags': {}}
        from_db = flag.get_flag_for_entry(ent, 'interesting')
        h.assert_equal(from_db['count'], 0)
        h.assert_equal(len(from_db['flaggings']), 0)

    def test_get_flag_for_entry(self):
        f = {'count': 1, 'flaggings': [{}]}
        ent = {'_id': 'entryid', 'flags': {'interesting': f}}
        from_db = flag.get_flag_for_entry(ent, 'interesting')
        h.assert_equal(from_db['count'], 1)
        h.assert_equal(len(from_db['flaggings']), 1)

    @h.raises(KeyError)
    def test_get_unknown_flag(self):
        ent = {'_id': 'entryid'}
        flag.get_flag_for_entry(ent, 'somethingelse')

    def test_inc_flag_on_entry(self):
        ent = {'_id': 'entryid'}
        acc = {'_id': 'accountid'}

        Entry(ent).save()
        account.create(acc)

        flag.inc_flag(ent, 'interesting', acc)

        flobj = Entry.find_one({'_id': ent['_id']})['flags']['interesting']
        h.assert_equal(len(flobj['flaggings']), 1)
        f = flobj['flaggings'][0]
        h.assert_equal(f['account'], 'accountid')
        delta = datetime.datetime.now() - f['time']
        h.assert_less(delta.seconds, 10)

    def test_inc_flag_on_account(self):
        ent = {'_id': 'entryid'}
        acc = {'_id': 'accountid'}

        Entry(ent).save()
        _id = account.create(acc)

        flag.inc_flag(ent, 'interesting', acc)

        from_db = account.get(_id)['flags']
        h.assert_equal(len(from_db), 1)
        f = from_db[0]
        h.assert_equal(f['type'], 'entry')
        h.assert_equal(f['_id'], 'entryid')
        h.assert_equal(f['flag'], 'interesting')
        delta = datetime.datetime.now() - f['time']
        h.assert_less(delta.seconds, 10)
