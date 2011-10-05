
from openspending.model import meta as db
from openspending.model.attribute import Attribute
from openspending.model.common import TableHandler

class Dimension(object):
    """ A base class for dimensions. """

    def __init__(self, dataset, name, data):
        self._data = data
        self.dataset = dataset
        self.name = name
        self.label = data.get('label', name)
        self.facet = data.get('facet')

    def join(self, from_clause):
        """ Return the object to be joined in when this dimension
        is part of a query. """
        return from_clause

    def flush(self, bind):
        """ Only applies to dimensions with their own table. """
        pass

    def drop(self, bind):
        """ Only applies to dimensions with their own table. """
        del self.column

    def __getitem__(self, name):
        """ Only applies to dimensions with their own attributes. 
        """
        raise KeyError()

    def __repr__(self):
        return "<Dimension(%s)>" % self.name

class AttributeDimension(Dimension, Attribute):
    """ A simple dimension that does not create its own values table 
    but keeps its values directly as columns on the facts table. 
    """

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, data)
        Dimension.__init__(self, dataset, name, data)
    
    def __repr__(self):
        return "<AttributeDimension(%s)>" % self.name

class Measure(Attribute):
    """ A value on the facts table that can be subject to aggregation, 
    and is specific to this one fact. """

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, data)
        self.name = name
        self.label = data.get('label', name)

    def __getitem__(self, name):
        raise KeyError()

    def __repr__(self):
        return "<Metric(%s)>" % self.name

class CompoundDimension(Dimension, TableHandler):
    """ A compound dimension is an outer table on the star schema, i.e. an
    associated table that is referenced from the fact table. It can have 
    any number of attributes but in the case of OpenSpending it will not 
    have sub-dimensions (i.e. snowflake schema).
    """

    def __init__(self, dataset, name, data):
        Dimension.__init__(self, dataset, name, data)
        self.taxonomy = data.get('taxonomy', 'entity')

        attributes =  data.get('fields', [])
        # TODO: this needs to be done in validation!
        names = [a['name'] for a in attributes]
        if 'name' not in names and 'label' in names:
            for a in attributes:
                if a['name'] == 'label':
                    a = a.copy()
                    a['name'] = 'name'
                    a['datatype'] = 'id'
                    attributes.append(a)
                    break

        self.attributes = []
        for attr in attributes:
            self.attributes.append(Attribute(self, attr))

    def join(self, from_clause):
        """ This will return a query fragment that can be used to establish
        a join between the scheme table and the dimension, aliased to 
        represent this dimension (i.e. there can be multiple joins to the 
        same table from different dimensions).
        """
        return from_clause.join(self.alias, self.alias.c.id==self.column_alias)
    
    def flush(self, bind):
        self._flush(bind)
    
    def drop(self, bind):
        self._drop(bind)
        del self.column

    @property
    def column_alias(self):
        """ This an aliased pointer to the FK column on the fact table. """
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
        """ Create the table and column associated with this dimension 
        if it does not already exist and propagate this call to the 
        associated attributes. 
        """
        self._ensure_table(meta, self.dataset.name + '_' + self.taxonomy)
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
        """ Load a row of data into this dimension by having the attributes
        perform type casting and then upserting the values. 
        """
        dim = dict()
        for attr in self.attributes:
            dim.update(attr.load(bind, row))
        pk = self._upsert(bind, dim, ['name'])
        return {self.column.name: pk}

    def __repr__(self):
        return "<CompoundDimension(%s/%s:%s)>" % (self.scheme, self.name, 
                                                 self.attributes)



