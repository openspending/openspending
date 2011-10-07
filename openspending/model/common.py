from json import dumps, loads
from sqlalchemy.types import Text, MutableType, TypeDecorator

from openspending.model import meta as db 

class JSONType(MutableType, TypeDecorator):
    impl = Text

    def __init__(self):
        super(JSONType, self).__init__()

    def process_bind_param(self, value, dialect):
        return dumps(value)

    def process_result_value(self, value, dialiect):
        return loads(value)

    def copy_value(self, value):
        return loads(dumps(value))


class TableHandler(object):
    """ Used by automatically generated objects such as datasets
    and dimensions to generate, write and clear the table under 
    its management. """

    def _ensure_table(self, meta, name, id_type=db.Integer):
        """ Create the given table if it does not exist, otherwise
        reflect the current table schema from the database.
        """
        if not meta.bind.has_table(name):
            self.table = db.Table(name, meta)
            col = db.Column('id', id_type, primary_key=True)
            self.table.append_column(col)
            self.table.create(meta.bind)
        else:
            self.table = db.Table(name, meta, autoload=True)

    def _upsert(self, bind, data, unique_columns):
        """ Upsert a set of values into the table. This will 
        query for the set of unique columns and either update an 
        existing row or create a new one. In both cases, the ID
        of the changed row will be returned. 
        """
        key = db.and_(*[self.table.c[c]==data.get(c) for \
                c in unique_columns])
        q = self.table.update(key, data)
        if bind.execute(q).rowcount == 0:
            q = self.table.insert(data)
            rs = bind.execute(q)
            return rs.inserted_primary_key[0]
        else:
            q = self.table.select(key)
            row = bind.execute(q).fetchone()
            return row['id']

    def _flush(self, bind):
        """ Delete all rows in the table. """
        q = self.table.delete()
        bind.execute(q)

    def _drop(self, bind):
        """ Drop the table and the local reference to it. """
        if bind.has_table(self.table.name):
            self.table.drop()
        del self.table


