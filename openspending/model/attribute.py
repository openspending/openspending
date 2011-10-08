from openspending.model import meta as db

class Attribute(object):

    def __init__(self, parent, data):
        self._data = data
        self.parent = parent
        self.name = data.get('name')
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

    def generate(self, meta, table):
        """ Create the column on a given table, selecting the proper
        data type from attribute metadata. 
        """
        if self.name in table.c:
            self.column = table.c[self.name]
            return
        # TODO: fetch this from AttributeType system?
        types = {
            'string': db.UnicodeText,
            'constant': db.UnicodeText,
            'date': db.UnicodeText,
            'float': db.Float,
                }
        type_ = types.get(self.datatype, db.UnicodeText)
        self.column = db.Column(self.name, type_)
        self.column.create(table)

    def load(self, bind, value):
        """ Load an attribute value but perform type conversion first.
        """
        return {self.column.name: value}

    def __repr__(self):
        return "<Attribute(%s)>" % self.name
    
    def as_dict(self):
        return self._data
