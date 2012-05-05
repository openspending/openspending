from openspending.model import meta as db

class Attribute(object):
    """ An attribute describes some concrete value stored in the data model.
    This value can either be stored directly on the facts table or on a 
    separate dimension table, which is associated to the facts table through
    a reference. """

    def __init__(self, parent, name, data):
        self._data = data
        self.parent = parent
        self.name = name
        self.key = data.get('key', False)
        self.source_column = data.get('column')
        self.default_value = data.get('default_value')
        self.constant = data.get('constant')
        self.description = data.get('description')
        self.datatype = data.get('datatype', 'value')

    @property
    def selectable(self):
        return self.column_alias

    @property
    def column_alias(self):
        return self.parent.alias.c[self.column.name]

    def init(self, meta, table, make_table=False):
        """ Make a model for this attribute, selecting the proper
        data type from attribute metadata.
        """
        # TODO: fetch this from AttributeType system?
        types = {
            'string': db.UnicodeText,
            'constant': db.UnicodeText,
            'date': db.UnicodeText,
            'float': db.Float,
                }
        type_ = types.get(self.datatype, db.UnicodeText)
        column = db.Column(self.name, type_)
        table.append_column(column)
        return column

    def generate(self, meta, table):
        """ Create the column on a given table. """
        pass

    def load(self, bind, value):
        return {self.column.name: value}

    def __repr__(self):
        return "<Attribute(%s)>" % self.name

    def as_dict(self):
        return self._data
