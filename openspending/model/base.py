import sys

from bson.dbref import DBRef
from pymongo.objectid import ObjectId, InvalidId

from openspending import mongo

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def dictproperty(name):
    def setter(self, value):
        self[name] = value
    getter = lambda self: self.get(name)
    return property(getter, setter)

class Base(dict):

    context = None

    @classproperty
    @classmethod
    def collection_name(cls):
        return cls.__name__.lower()

    @classproperty
    @classmethod
    def c(cls):
        return mongo.db[cls.collection_name]

    @classmethod
    def find(cls, *args, **kwargs):
        kwargs['as_class'] = cls
        return cls.c.find(*args, **kwargs)

    @classmethod
    def find_one(cls, *args, **kwargs):
        kwargs['as_class'] = cls
        return cls.c.find_one(*args, **kwargs)

    @classmethod
    def by_id(cls, _id):
        fl = [{'name': _id}, {'_id': _id}]
        try:
            fl.append({'_id': ObjectId(_id)})
        except:
            pass
        return cls.find_one({'$or': fl})

    def __init__(self, *args, **kwargs):
        # We cannot simply use dict's constructor, because dictproperties can
        # address keys other than their name. To see why this is a problem,
        # consider the following:
        #
        #     class Foo(Base):
        #         bar = dictproperty('baz')
        #
        #     foo_instance = Foo(bar=123)
        #
        # Here foo_instance *should* have foo_instance['baz'] == 123, but in
        # fact the dictproperty setter has been completely ignored and
        # foo_instance['bar'] has been set instead.

        d = dict(*args, **kwargs)

        for k, v in d.iteritems():
            if hasattr(self, k):
                # if setter defined, use it
                setattr(self, k, v)
            else:
                # fallback to setting as dict
                self[k] = v

    def __repr__(self):
        dr = super(Base, self).__repr__()
        return "<%s(%s)>" % (self.collection_name, dr)

    def __hash__(self):
        return hash(self.get('_id'))

    def to_ref(self):
        if self.id:
            return DBRef(self.collection_name, self.id)

    def to_ref_dict(self):
        d = dict(self.items())
        d['ref'] = self.to_ref()
        return d

    def copy(self):
        n = self.__class__()
        n.update(super(Base, self).copy())
        return n

    def save(self, **kwargs):
        self.c.save(self)

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
                fn_in_base = globals()[name]
            except KeyError:
                # Raise the original AttributeError, not this KeyError
                raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                # Delete exception info to prevent creating a cycle that
                # the garbage collector won't like
                del exc_info

            def _model_curry(*args, **kwargs):
                return fn_in_base(self.collection, *args, **kwargs)

            return _model_curry

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
        _q = {'$or': [_q, {'_id': ObjectId(obj['_id'])}]}
    except InvalidId:
        pass

    return _q

def get(collection, _id):
    """Get object in ``collection`` with _id ``_id``"""
    return mongo.db[collection].find_one(q({'_id': _id}))

def find(collection, spec=None, **kwargs):
    """Find objects from ``collection`` matching ``spec``"""
    return mongo.db[collection].find(spec, **kwargs)

def find_one(collection, spec=None):
    """Find one object from ``collection`` matching ``spec``"""
    return mongo.db[collection].find_one(spec)

def find_one_by(collection, key, value):
    """Find one object from ``collection`` where ``key`` == ``value``"""
    return mongo.db[collection].find_one({key: value})

def remove(collection, spec):
    """Remove objects from ``collection`` which match ``spec``"""
    return mongo.db[collection].remove(spec)

def create(collection, doc):
    """Insert a row into ``collection`` using ``doc``"""
    return mongo.db[collection].insert(doc, manipulate=True)

def update(collection, obj, doc):
    """Update object ``obj`` in ``collection`` using ``doc``"""
    return mongo.db[collection].update(q(obj), doc, upsert=True)

def save(collection, to_save):
    """Save document ``to_save`` to collection ``collection``"""
    return mongo.db[collection].save(to_save, manipulate=True)

