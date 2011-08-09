import datetime
import uuid

from . import base

collection = 'account'

base.init_model_module(__name__, collection)

# account objects probably have the following fields
#   _id
#   name
#   label
#   email
#   password_hash
#   api_key

def create(doc):
    """Create an account. Autogenerates an api_key"""
    doc['api_key'] = str(uuid.uuid4())
    return base.create(collection, doc)

def add_role(obj, rolename):
    """Add ``rolename`` to the set of roles possessed by this account"""
    return base.update(collection, obj, {'$addToSet': {'roles': rolename}})

