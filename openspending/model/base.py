import sys

from openspending import mongo

class ModelWrapper(object):
    def __init__(self, wrapped, collection):
        self.wrapped = wrapped
        self.collection = collection

    def __getattr__(self, name):
        try:
            return getattr(self.wrapped, name)
        except AttributeError:
            exc_info = sys.exc_info() # save the original error raised
            try:
                # First, try to find the attribute in base
                in_base = globals()[name]
            except KeyError:
                # Raise the original AttributeError, not this KeyError
                raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                # Delete exception info to prevent creating a cycle that
                # the garbage collector won't like
                del exc_info

            is_func = False
            if type(in_base) == type(lambda x: x):
                is_func = True
                def curry_in_base(*args, **kwargs):
                    return in_base(self.collection, *args, **kwargs)

            return curry_in_base if is_func else in_base

    def __repr__(self):
        return '<ModelWrapper for %s (%s)>' % (self.wrapped.__name__, self.collection)

class ModelError(Exception):
    pass

def init_model_module(name, collection):
    sys.modules[name] = ModelWrapper(sys.modules[name], collection)

def q(obj):
    """Return a query spec identifying the given object"""
    _q = {'_id': obj['_id']}
    try:
        _q = {'$or': [_q, {'_id': mongo.ObjectId(obj['_id'])}]}
    except mongo.InvalidId:
        pass

    return _q

def create(collection, doc):
    """\
    Insert a row into ``collection`` using ``doc``. Return the created
    document.\
    """
    return get(collection, insert(collection, doc))

def distinct(collection, key):
    """Get a list of distinct values for ``key`` among all documents in ``collection``"""
    return mongo.db[collection].distinct(key)

def find(collection, spec=None, **kwargs):
    """Find objects from ``collection`` matching ``spec``"""
    return mongo.db[collection].find(spec, **kwargs)

def find_one(collection, spec=None):
    """Find one object from ``collection`` matching ``spec``"""
    return mongo.db[collection].find_one(spec)

def find_one_by(collection, key, value):
    """Find one object from ``collection`` where ``key`` == ``value``"""
    return mongo.db[collection].find_one({key: value})

def get(collection, _id):
    """Get object in ``collection`` with _id ``_id``"""
    return mongo.db[collection].find_one(q({'_id': _id}))

def get_ref_dict(collection, doc):
    """\
    Return a ``ref_dict`` for ``doc`` in ``collection``. A ref dict contains
    one extra key, "ref", which has as its value a mongo DBRef pointing to the
    relevant document in collection ``collection``.\
    """
    d = doc.copy()
    d['ref'] = mongo.DBRef(collection, d['_id'])
    return d

def insert(collection, doc):
    """Insert a row into ``collection`` using ``doc``"""
    return mongo.db[collection].insert(doc, manipulate=True)

def remove(collection, spec):
    """Remove objects from ``collection`` which match ``spec``"""
    return mongo.db[collection].remove(spec)

def save(collection, to_save):
    """Save document ``to_save`` to collection ``collection``"""
    return mongo.db[collection].save(to_save, manipulate=True)

def update(collection, spec, doc, **kwargs):
    """Update object(s) matching ``spec`` in ``collection`` using ``doc``"""
    if '_id' in spec:
        spec = q(spec)
    return mongo.db[collection].update(spec, doc, **kwargs)

