
from openspending.model import meta as db
from openspending.model.attribute import Attribute
from openspending.model.common import TableHandler

class Dimension(object):

    def __init__(self, dataset, name, data):
        self._data = data
        self.dataset = dataset
        self.name = name
        self.label = data.get('label', name)
        self.facet = data.get('facet')

    def join(self, from_clause):
        return from_clause

    def flush(self, bind):
        pass

    def drop(self, bind):
        del self.column

    def __getitem__(self, name):
        raise KeyError()

    def __repr__(self):
        return "<Dimension(%s)>" % self.name

class ValueDimension(Dimension, Attribute):

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, data)
        Dimension.__init__(self, dataset, name, data)
    
    def __repr__(self):
        return "<ValueDimension(%s)>" % self.name

class Metric(Attribute):

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, data)
        self.name = name
        self.label = data.get('label', name)

    def join(self, from_clause):
        return from_clause

    def flush(self, bind):
        pass

    def drop(self, bind):
        pass

    def __getitem__(self, name):
        raise KeyError()

    def __repr__(self):
        return "<Metric(%s)>" % self.name

class ComplexDimension(Dimension, TableHandler):

    def __init__(self, dataset, name, data):
        Dimension.__init__(self, dataset, name, data)
        self.scheme = data.get('scheme', data.get('taxonomy', 'entity'))
        self.attributes = []
        for attr in data.get('attributes', data.get('fields', [])):
            self.attributes.append(Attribute(self, attr))

    def join(self, from_clause):
        return from_clause.join(self.alias, self.alias.c.id==self.column_alias)
    
    def flush(self, bind):
        self._flush(bind)
    
    def drop(self, bind):
        self._drop(bind)
        del self.column

    @property
    def column_alias(self):
        return self.dataset.alias.c[self.column.name]

    @property
    def selectable(self):
        return self.alias

    def __getitem__(self, name):
        for attr in self.attributes:
            if attr.name == name:
                return attr
        raise KeyError()

    def generate(self, meta, entry_table):
        self._ensure_table(meta, self.dataset.name + '_' + self.scheme)
        for attr in self.attributes:
            attr.generate(meta, self.table)
        fk = self.name + '_id'
        if not fk in entry_table.c:
            self.column = db.Column(self.name + '_id', db.Integer, index=True)
            self.column.create(entry_table, index_name=self.name + '_id_index')
        else:
            self.column = entry_table.c[fk]
        self.alias = self.table.alias(self.name)

    def load(self, bind, row):
        dim = dict()
        for attr in self.attributes:
            dim.update(attr.load(bind, row))
        pk = self._upsert(bind, dim, ['name'])
        return {self.column.name: pk}

    def __repr__(self):
        return "<ComplexDimension(%s/%s:%s)>" % (self.scheme, self.name, 
                                                 self.attributes)



