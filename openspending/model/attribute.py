from openspending.model import meta as db

class Attribute(object):

    def __init__(self, parent, data):
        self._data = data
        self.parent = parent
        self.name = data.get('name')
        self.source_column = data.get('column')
        self.default = data.get('default', data.get('constant'))
        self.description = data.get('description')
        self.datatype = data.get('datatype')

    @property
    def selectable(self):
        return self.column_alias

    @property
    def column_alias(self):
        return self.parent.alias.c[self.column.name]

    def generate(self, meta, table):
        if self.name in table.c:
            self.column = table.c[self.name]
            return
        types = {
            'string': db.UnicodeText,
            'constant': db.UnicodeText,
            'date': db.UnicodeText,
            'float': db.Float,
                }
        type_ = types.get(self.datatype, db.UnicodeText)
        self.column = db.Column(self.name, type_)
        self.column.create(table)

    def load(self, bind, row):
        value = row.get(self.source_column, self.default) if \
                self.source_column else self.default
        return {self.column.name: value.decode('utf-8') if value else None}

    def __repr__(self):
        return "<Attribute(%s)>" % self.name

