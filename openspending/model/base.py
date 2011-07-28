from bson.dbref import DBRef
from pymongo.objectid import ObjectId

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
    def by_id(cls, id):
        fl = [{'name': id}, {'_id': id}]
        try:
            fl.append({'_id': ObjectId(id)})
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

    def to_query_dict(self, sep='.'):
        """ Flatten down a dictionary with some smartness. """
        def _flatten(orig):
            flat = {}
            for k, v in orig.items():
                if isinstance(v, dict):
                    for sk, sv in _flatten(v).items():
                        flat[k + sep + sk] = sv
                else:
                    flat[k] = v
            return flat
        return _flatten(self)

    def to_index_dict(self):
        query_form = self.to_query_dict()
        index_form = {}
        for k, v in query_form.items():
            k = k.replace('$', '')
            if k.endswith('._id'):
                k = k.replace('._id', '.id')
            if k.endswith('.name'):
                ck = k.replace('.name', '')
                if not ck in query_form.keys():
                    index_form[ck] = v
            index_form[k] = v
        return index_form

def q(obj):
    """Return a query spec identifying the given object"""
    return {'_id': obj['_id']}

def create(collection, doc):
    """Insert a row into the specified collection using ``doc``"""
    return mongo.db[collection].insert(doc, manipulate=True)

def update(collection, obj, doc):
    return mongo.db[collection].update(q(obj), doc, upsert=True)

def find(collection, spec):
    return mongo.db[collection].find(spec)

def find_one_by(collection, key, value):
    """Find one object from the specified collection where key=value"""
    return mongo.db[collection].find_one({key: value})
