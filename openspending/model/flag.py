import datetime

from .. import model

AVAILABLE_FLAGS = {
    "interesting": "Interesting",
    "erroneous": "Erroneous"
}

def get_flag_for_entry(entry, flag_name):
    _chk_flag(flag_name)

    if 'flags' not in entry:
        entry['flags'] = _get_default_flags()
        model.entry.update(entry, {'$set': {'flags': entry['flags']}})

    if flag_name not in entry['flags']:
        entry['flags'][flag_name] = _get_flag_template()
        model.entry.update(
            entry,
            {'$set': {'flags.%s' % flag_name: entry['flags'][flag_name]}}
        )

    return entry['flags'][flag_name]

def inc_flag(entry, flag_name, account):
    _chk_flag(flag_name)

    if has_flagged(entry, flag_name, account):
        return False

    tstamp = datetime.datetime.now()

    ent_flag = {
        'time': tstamp,
        'account': account['_id']
    }
    acc_flag = {
        'time': tstamp,
        'type': 'entry',
        '_id': entry['_id'],
        'flag': flag_name
    }

    model.entry.update(
        entry,
        {
            '$inc': {'flags.%s.count' % flag_name: 1},
            '$push': {'flags.%s.flaggings' % flag_name: ent_flag}
        }
    )
    model.account.update(account, {'$push': {'flags': acc_flag}})

    return True

def has_flagged(entry, flag_name, account):
    if flag_name not in AVAILABLE_FLAGS:
        return False

    return any((x['account'] == account['_id']
                for x in get_flag_for_entry(entry, flag_name)['flaggings']))

def _chk_flag(flag_name):
    if flag_name not in AVAILABLE_FLAGS:
        raise KeyError("Unknown flag!")

def _get_flag_template():
    return {"count": 0, "flaggings": []}

def _get_default_flags():
    return dict([(name, _get_flag_template()) for name in AVAILABLE_FLAGS])