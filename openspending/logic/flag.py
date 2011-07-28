import datetime

from openspending.model import Entry, account

AVAILABLE_FLAGS = {
    "interesting": "Interesting",
    "erroneous": "Erroneous"
}


def get_flag_template():
    return  {"count": 0, "flaggings": []}

def get_default_flags():
    return dict([(name, get_flag_template()) for name in AVAILABLE_FLAGS])

def add_flag(flag_name):
    Entry.c.update({"flags": {"$exists": False}}, {"$set": {"flags":
        get_default_flags()}}, multi=True)
    Entry.c.update({"flags": {"$exists": True}, "flags.%s" % flag_name:
        {"$exists": False}}, {"$set": {"flags.%s" % flag_name: get_flag_template()}}, multi=True)

def get_flag_for_entry(entry, flag_name):
    if flag_name not in AVAILABLE_FLAGS:
        raise KeyError("Unknown flag!")
    if not 'flags' in entry or entry['flags'] is None or not entry['flags']:
        entry['flags'] = get_default_flags()
        Entry.c.update({"_id": entry.id}, {"$set": {"flags":
            get_default_flags()}})
    if flag_name not in entry['flags']:
        entry['flags'][flag_name] = get_flag_template()
        Entry.c.update({"_id": entry.id}, {"$set":
            {"flags.%s" % flag_name: get_flag_template()}})
    return entry['flags'].get(flag_name)

def inc_flag(entry, flag_name, acc):
    if flag_name not in AVAILABLE_FLAGS:
        raise KeyError("Unknown flag!")
    if has_flagged(entry, flag_name, acc):
        return False
    Entry.c.update({"_id": entry.id}, {"$inc": {"flags.%s.count" %
        flag_name: 1}, "$push": {"flags.%s.flaggings" % flag_name: {
            "time": datetime.datetime.now(),
            "account": acc['_id']}}
        })
    account.add_flag(acc, entry, flag_name)

    return True

def has_flagged(entry, flag_name, account):
    if flag_name not in AVAILABLE_FLAGS:
        return False
    return any((x['account'] == account.id for x in get_flag_for_entry(entry, flag_name)['flaggings']))
