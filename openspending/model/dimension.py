
from openspending.model import meta as db
from openspending.model.attribute import Attribute
from openspending.model.common import TableHandler, ALIAS_PLACEHOLDER


class Dimension(object):
    """ A base class for dimensions. A dimension is any property of an entry
    that can serve to describe it beyond its purely numeric ``Measure``.  """

    def __init__(self, dataset, name, data):
        self._data = data
        self.dataset = dataset
        self.name = name
        self.key = data.get('key', False)
        self.label = data.get('label', name)
        self.type = data.get('type', name)
        self.description = data.get('description', name)
        self.facet = data.get('facet')

    def join(self, from_clause):
        return from_clause

    def flush(self, bind):
        pass

    def drop(self, bind):
        del self.column

    @property
    def is_compound(self):
        """ Test whether or not this dimension object is compound. """
        return isinstance(self, CompoundDimension)

    def __getitem__(self, name):
        raise KeyError()

    def __repr__(self):
        return "<Dimension(%s)>" % self.name

    def as_dict(self):
        # FIXME: legacy support
        d = self._data.copy()
        d['key'] = self.name
        d['name'] = self.name
        return d


class AttributeDimension(Dimension, Attribute):
    """ A simple dimension that does not create its own values table
    but keeps its values directly as columns on the facts table. This is
    somewhat unusual for a star schema but appropriate for properties such as
    transaction identifiers whose cardinality roughly equals that of the facts
    table.
    """

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, name, data)
        Dimension.__init__(self, dataset, name, data)

    def __repr__(self):
        return "<AttributeDimension(%s)>" % self.name

    def members(self, conditions="1=1", limit=None, offset=0):
        """ Get a listing of all the members of the dimension (i.e. all the
        distinct values) matching the filter in ``conditions``. """
        query = db.select([self.column_alias], conditions,
            limit=limit, offset=offset, distinct=True)
        rp = self.dataset.bind.execute(query)
        while True:
            row = rp.fetchone()
            if row is None:
                break
            yield row[0]

    def num_entries(self, conditions="1=1"):
        """ Return the count of entries on the dataset fact table having the
        dimension set to a value matching the filter given by ``conditions``.
        """
        query = db.select([db.func.count(db.func.distinct(self.column_alias))],
                          conditions)
        rp = self.dataset.bind.execute(query)
        return rp.fetchone()[0]


class Measure(Attribute):
    """ A value on the facts table that can be subject to aggregation,
    and is specific to this one fact. This would typically be some
    financial unit, i.e. the amount associated with the transaction or
    a specific portion thereof (i.e. co-financed amounts). """

    def __init__(self, dataset, name, data):
        Attribute.__init__(self, dataset, name, data)
        self.label = data.get('label', name)

    def __getitem__(self, name):
        raise KeyError()

    def join(self, from_clause):
        return from_clause

    def __repr__(self):
        return "<Measure(%s)>" % self.name


class CompoundDimension(Dimension, TableHandler):
    """ A compound dimension is an outer table on the star schema, i.e. an
    associated table that is referenced from the fact table. It can have
    any number of attributes but in the case of OpenSpending it will not
    have sub-dimensions (i.e. snowflake schema).
    """

    def __init__(self, dataset, name, data):
        Dimension.__init__(self, dataset, name, data)
        self.taxonomy = data.get('taxonomy', name)

        self.attributes = []
        for name, attr in data.get('attributes', {}).items():
            self.attributes.append(Attribute(self, name, attr))

        # TODO: possibly use a LRU later on?
        self._pk_cache = {}

    def join(self, from_clause):
        """ This will return a query fragment that can be used to establish
        an aliased join between the fact table and the dimension table.
        """
        return from_clause.join(self.alias, self.alias.c.id == self.column_alias)

    def flush(self, bind):
        """ Clear all data in the dimension table but keep the table structure
        intact. """
        self._flush(bind)

    def drop(self, bind):
        """ Drop the dimension table and all data within it. """
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

    def init(self, meta, fact_table, make_table=True):
        column = db.Column(self.name + '_id', db.Integer, index=True)
        fact_table.append_column(column)
        if make_table is True:
            self._init_table(meta, self.dataset.name, self.name)
            for attr in self.attributes:
                attr.column = attr.init(meta, self.table)
            alias_name = self.name.replace('_', ALIAS_PLACEHOLDER)
            self.alias = self.table.alias(alias_name)
        return column

    def generate(self, meta, entry_table):
        """ Create the table and column associated with this dimension
        if it does not already exist and propagate this call to the
        associated attributes.
        """
        for attr in self.attributes:
            attr.generate(meta, self.table)
        self._generate_table()

    def load(self, bind, row):
        """ Load a row of data into this dimension by upserting the attribute
        values. """
        dim = dict()
        for attr in self.attributes:
            attr_data = row[attr.name]
            dim.update(attr.load(bind, attr_data))
        name = dim['name']
        if name in self._pk_cache:
            pk = self._pk_cache[name]
        else:
            pk = self._upsert(bind, dim, ['name'])
            self._pk_cache[name] = pk
        return {self.column.name: pk}

    def members(self, conditions="1=1", limit=None, offset=0):
        """ Get a listing of all the members of the dimension (i.e. all the
        distinct values) matching the filter in ``conditions``. This can also be
        used to find a single individual member, e.g. a dimension value
        identified by its name. """
        query = db.select([self.alias], conditions,
            limit=limit, offset=offset,
            distinct=True)
        rp = self.dataset.bind.execute(query)
        while True:
            row = rp.fetchone()
            if row is None:
                break
            member = dict(row.items())
            member['taxonomy'] = self.taxonomy
            yield member

    def num_entries(self, conditions="1=1"):
        """ Return the count of entries on the dataset fact table having the
        dimension set to a value matching the filter given by ``conditions``.
        """
        joins = self.join(self.dataset.alias)
        query = db.select([db.func.count(db.func.distinct(self.column_alias))],
                          conditions, joins)
        rp = self.dataset.bind.execute(query)
        return rp.fetchone()[0]


    def __len__(self):
        rp = self.dataset.bind.execute(self.alias.count())
        return rp.fetchone()[0]

    def __repr__(self):
        return "<CompoundDimension(%s:%s)>" % (self.name, self.attributes)

class DateDimension(CompoundDimension):
    """ DateDimensions are closely related to :py:class:`CompoundDimensions`
    but the value is set up from a Python date object to automatically contain
    several properties of the date in their own attributes (e.g. year, month,
    quarter, day). """

    DATE_ATTRIBUTES = {
            'name': { 'datatype': 'string'},
            'label': {'datatype': 'string'},
            'year': {'datatype': 'string'},
            'quarter': {'datatype': 'string'},
            'month': {'datatype': 'string'},
            'week': {'datatype': 'string'},
            'day': {'datatype': 'string'},
            # legacy query support:
            'yearmonth': {'datatype': 'string'},
        }

    def __init__(self, dataset, name, data):
        Dimension.__init__(self, dataset, name, data)
        self.taxonomy = name

        self.attributes = []
        for name, attr in self.DATE_ATTRIBUTES.items():
            self.attributes.append(Attribute(self, name, attr))

        self._pk_cache = {}

    def load(self, bind, value):
        """ Given a Python datetime.date, generate a date dimension with the
        following attributes automatically set:

        * name - a human-redable representation
        * year - the year only (e.g. 2011)
        * quarter - a number to identify the quarter of the year (zero-based)
        * month - the month of the date (e.g. 01)
        * week - calendar week of the year (e.g. 42)
        * day - day of the month (e.g. 8)
        * yearmonth - combined year and month (e.g. 201112)
        """
        data = {
                'name': value.isoformat(),
                'label': value.strftime("%d. %B %Y"),
                'year': value.strftime('%Y'),
                'quarter': str(value.month / 4),
                'month': value.strftime('%m'),
                'week': value.strftime('%W'),
                'day': value.strftime('%d'),
                'yearmonth': value.strftime('%Y%m')
            }
        return super(DateDimension, self).load(bind, data)

    def __repr__(self):
        return "<DateDimension(%s:%s)>" % (self.name, self.attributes)
