from collections import defaultdict

from openspending.model import meta as db

from openspending.model.common import TableHandler, JSONType
from openspending.model.dimension import ComplexDimension, ValueDimension
from openspending.model.dimension import Metric


class Dataset(TableHandler, db.Model):
    __tablename__ = 'dataset'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True)
    label = db.Column(db.Unicode(2000))
    description = db.Column(db.Unicode())
    currency = db.Column(db.Unicode())
    data = db.Column(JSONType, default=dict)

    def __init__(self, data):
        self.data = data
        dataset = data.get('dataset', {})
        self.label = dataset.get('label')
        self.name = dataset.get('name')
        self.description = dataset.get('description')
        self.currency = dataset.get('currency')
        self._load_model()

    @db.reconstructor
    def _load_model(self):
        self.dimensions = []
        self.metrics = []
        for dim, data in self.data.get('mapping', {}).items():
            if data.get('type') == 'metric' or dim == 'amount':
                self.metrics.append(Metric(self, dim, data))
                continue
            elif data.get('type', 'value') == 'value':
                dimension = ValueDimension(self, dim, data)
            else:
                dimension = ComplexDimension(self, dim, data)
            self.dimensions.append(dimension)

    def __getitem__(self, name):
        """ Access a field (dimension or metric) by name. """
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError()

    @property
    def fields(self):
        """ Both the dimensions and metrics in this dataset. """
        return self.dimensions + self.metrics

    def generate(self):
        """ Create the main entity table for this dataset. """
        self.bind = db.engine
        self.meta = db.MetaData()
        self.meta.bind = self.bind

        self._ensure_table(self.meta, self.name + '_entry')
        for field in self.fields:
            field.generate(self.meta, self.table)
        self.alias = self.table.alias('entry')

    def load(self, row):
        entry = dict()
        for field in self.fields:
            entry.update(field.load(self.bind, row))
        self._upsert(self.bind, entry, ['id'])

    def load_all(self, rows):
        for row in rows:
            self.load(row)
        #bind.commit()

    def flush(self):
        for field in self.fields:
            field.flush(self.bind)
        self._flush(self.bind)

    def drop(self):
        for field in self.fields:
            field.drop(self.bind)
        self._drop(self.bind)

    def key(self, key):
        """ For a given ``key``, find a column to indentify it in a query.
        A ``key`` is either the name of a simple attribute (e.g. ``time``)
        or of an attribute of a complex dimension (e.g. ``to.label``). The
        returned key is using an alias, so it can be used in a query 
        directly. """
        attr = None
        if '.' in key:
            key, attr = key.split('.', 1)
        dimension = self[key]
        if hasattr(dimension, 'alias'):
            attr_name = dimension[attr].column.name if attr else 'id'
            return dimension.alias.c[attr_name]
        return self.alias.c[dimension.column.name]

    def materialize(self, conditions="1=1", order_by=None):
        """ Generate a fully denormalized view of the entries on this 
        table. """
        joins = self.alias
        for f in self.fields:
            joins = f.join(joins)
        query = db.select([f.selectable for f in self.fields], 
                       conditions, joins, order_by=order_by,
                       use_labels=True)
        rp = self.bind.execute(query)
        while True:
            row = rp.fetchone()
            if row is None:
                break
            result = {}
            for k, v in row.items():
                field, attr = k.split('_', 1)
                if field == 'entry':
                    result[attr] = v
                else:
                    if not field in result:
                        result[field] = dict()
                    result[field][attr] = v
            yield result

    def aggregate(self, metric='amount', drilldowns=None, cuts=None, 
            page=1, pagesize=10000, order=None):

        cuts = cuts or []
        drilldowns = drilldowns or []
        joins = self.alias
        for dimension in set(drilldowns + [k for k,v in cuts]):
            joins = self[dimension.split('.')[0]].join(joins)

        group_by = []
        fields = [db.func.sum(self.alias.c.amount).label(metric), 
                  db.func.count(self.alias.c.id).label("entries")]
        for key in drilldowns:
            column = self.key(key)
            if '.' in key or column.table == self.alias:
                fields.append(column)
            else:
                fields.append(column.table)
            group_by.append(column)
     
        conditions = db.and_()
        filters = defaultdict(set)
        for key, value in cuts:
            column = self.key(key)
            filters[column].add(value)
        for attr, values in filters.items():
            conditions.append(db.or_(*[attr==v for v in values]))

        order_by = []
        for key, direction in order or []:
            # TODO: handle case in which order criterion is not joined.
            column = self.key(key)
            order_by.append(column.desc() if direction else column.asc())

        query = db.select(fields, conditions, joins,
                       order_by=order_by or [metric + ' desc'],
                       group_by=group_by, use_labels=True)
        #print query
        summary = {metric: 0.0, 'num_entries': 0}
        drilldown = []
        rp = self.bind.execute(query)
        while True:
            row = rp.fetchone()
            if row is None:
                break
            result = {}
            for key, value in row.items():
                if key == metric:
                    summary[metric] += value
                if key == 'entries':
                    summary['num_entries'] += value
                if '_' in key:
                    dimension, attribute = key.split('_', 1)
                    if dimension == 'entry':
                        result[attribute] = value
                    else:
                        if not dimension in result:
                            result[dimension] = {}
                        result[dimension][attribute] = value
                else:
                    if key == 'entries':
                        key = 'num_entries'
                    result[key] = value
            drilldown.append(result)
        offset = ((page-1)*pagesize)
        return {'drilldown': drilldown[offset:offset+pagesize],
                'summary': summary}

    def __repr__(self):
        return "<Dataset(%s:%s:%s)>" % (self.name, self.dimensions,
                self.metrics)


