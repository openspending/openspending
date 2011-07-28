import datetime

from .entry import Entry
from .import account

AVAILABLE_FLAGS = {
    "interesting": "Interesting",
    "erroneous": "Erroneous"
}

def get_flag_for_entry(entry, flag_name):
    _chk_flag(flag_name)

    if 'flags' not in entry:
        entry['flags'] = _get_default_flags()
        Entry.c.update(
            {'_id': entry['_id']},
            {'$set': {'flags': entry['flags']}}
        )

    if flag_name not in entry['flags']:
        entry['flags'][flag_name] = _get_flag_template()
        Entry.c.update(
            {'_id': entry['_id']},
            {'$set': {'flags.%s' % flag_name: entry['flags'][flag_name]}}
        )

    return entry['flags'][flag_name]

def inc_flag(entry, flag_name, acc):
    _chk_flag(flag_name)

    if has_flagged(entry, flag_name, acc):
        return False

    tstamp = datetime.datetime.now()

    ent_flag = {
        'time': tstamp,
        'account': acc['_id']
    }
    acc_flag = {
        'time': tstamp,
        'type': 'entry',
        '_id': entry['_id'],
        'flag': flag_name
    }

    Entry.c.update(
        {'_id': entry['_id']},
        {
            '$inc': {'flags.%s.count' % flag_name: 1},
            '$push': {'flags.%s.flaggings' % flag_name: ent_flag}
        }
    )
    account.update(acc, {'$push': {'flags': acc_flag}})

    return True

def has_flagged(entry, flag_name, acc):
    if flag_name not in AVAILABLE_FLAGS:
        return False
    return any((x['account'] == acc['_id'] for x in get_flag_for_entry(entry, flag_name)['flaggings']))

def _chk_flag(flag_name):
    if flag_name not in AVAILABLE_FLAGS:
        raise KeyError("Unknown flag!")

def _get_flag_template():
    return {"count": 0, "flaggings": []}

def _get_default_flags():
    return dict([(name, _get_flag_template()) for name in AVAILABLE_FLAGS])