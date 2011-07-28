import datetime
import uuid

from . import base

collection = 'account'

# account objects probably have the following fields
#   _id
#   name
#   label
#   email
#   password_hash
#   api_key

def get(_id):
    """Get the account with _id ``_id``"""
    return base.find_one_by(collection, '_id', _id)

def find(spec):
    return base.find(collection, spec)

def find_one_by(key, value):
    """Find one account where ``key``==``value``"""
    return base.find_one_by(collection, key, value)

def create(doc):
    """Create a new account ``doc``"""
    doc['api_key'] = str(uuid.uuid4())
    return base.create(collection, doc)

def update(obj, doc):
    """Update object ``obj`` using ``doc``"""
    return base.update(collection, obj, doc)

def add_role(obj, rolename):
    """Add ``rolename`` to the set of roles possessed by this account"""
    return update(obj, {'$addToSet': {'roles': rolename}})

def add_flag(obj, entry, flag_name):
    """Add a note of a flagging on an account"""
    flag = {
        'time': datetime.datetime.now(),
        'type': 'entry',
        '_id': entry['_id'],
        'flag': flag_name
    }
    return update(obj, {'$push': {'flags': flag}})
