import math
from collections import defaultdict

from openspending.model import meta as db

from openspending.model.common import TableHandler, JSONType
from openspending.model.dimension import CompoundDimension, AttributeDimension
from openspending.model.dimension import Measure


class Dataset(TableHandler, db.Model):
    """ The dataset is the core entity of any access to data. All
    requests to the actual data store are routed through it, as well
    as data loading and model generation.

    The dataset keeps an in-memory representation of the data model
    (including all dimensions and measures) which can be used to 
    generate necessary queries.
    """
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
        """ Construct the in-memory object representation of this
        dataset's dimension and measures model.

        This is called upon initialization and deserialization of
        the dataset from the SQLAlchemy store.
        """
        self.dimensions = []
        self.measures = []
        for dim, data in self.data.get('mapping', {}).items():
            if data.get('type') == 'measure' or dim == 'amount':
                self.measures.append(Measure(self, dim, data))
                continue
            elif data.get('type', 'value') == 'value':
                dimension = AttributeDimension(self, dim, data)
            else:
                dimension = CompoundDimension(self, dim, data)
            self.dimensions.append(dimension)
        self.generate()

    def __getitem__(self, name):
        """ Access a field (dimension or measure) by name. """
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError()

    @property
    def fields(self):
        """ Both the dimensions and metrics in this dataset. """
        return self.dimensions + self.measures

    def generate(self):
        """ Create the tables and columns necessary for this dataset
        to keep data. Since this will also create references to these
        tables and columns in the model representation, this needs to
        be called even for access to the data, not just upon loading.
        """
        self.bind = db.engine
        self.meta = db.MetaData()
        self.meta.bind = self.bind

        self._ensure_table(self.meta, self.name + '_entry')
        for field in self.fields:
            field.generate(self.meta, self.table)
        self.alias = self.table.alias('entry')

    def load(self, row):
        """ Handle a single entry of data in the mapping source format, 
        i.e. with all needed columns. This will propagate to all dimensions
        and set values as appropriate. """
        entry = dict()
        for field in self.fields:
            entry.update(field.load(self.bind, row))
        self._upsert(self.bind, entry, ['id'])

    def load_all(self, rows):
        """ Non-API. 
        Mini-loader which does not replace a proper BaseImporter, consumes
        an iterable and loads each item in sequence. 
        """
        for row in rows:
            self.load(row)
        #bind.commit()

    def flush(self):
        """ Delete all data from the dataset tables but leave the table
        structure intact.
        """
        for dimension in self.dimensions:
            dimension.flush(self.bind)
        self._flush(self.bind)

    def drop(self):
        """ Drop all tables created as part of this dataset, i.e. by calling
        ``generate()``. This will of course also delete the data itself.
        """
        for dimension in self.dimensions:
            dimension.drop(self.bind)
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

    def materialize(self, conditions="1=1", order_by=None, limit=None,
            offset=None):
        """ Generate a fully denormalized view of the entries on this 
        table. This view is nested so that each dimension will be a hash
        of its attributes. 

        This is somewhat similar to the entries collection in the fully
        denormalized schema before OpenSpending 0.11 (MongoDB).
        """
        joins = self.alias
        for d in self.dimensions:
            joins = d.join(joins)
        selects = [f.selectable for f in self.fields] + [self.alias.c.id]
        query = db.select(selects, conditions, joins, order_by=order_by,
                          use_labels=True, limit=limit, offset=offset)
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

                        # TODO: backwards-compat?
                        if isinstance(self[field], CompoundDimension):
                            result[field]['taxonomy'] = self[field].taxonomy
                    result[field][attr] = v
            yield result

    def aggregate(self, measure='amount', drilldowns=None, cuts=None, 
            page=1, pagesize=10000, order=None):
        """ Query the dataset for a subset of cells based on cuts and 
        drilldowns. It returns a structure with a list of drilldown items 
        and a summary about the slice cutted by the query.

        ``measure``
            The numeric unit to be aggregated over, defaults to ``amount``.
        ``drilldowns``
            Dimensions to drill down to. (type: `list`)
        ``cuts``
            Specification what to cut from the cube. This is a
            `list` of `two-tuples` where the first item is the dimension
            and the second item is the value to cut from. It is turned into
            a query where multible cuts for the same dimension are combined
            to an *OR* query and then the queries for the different
            dimensions are combined to an *AND* query.
        ``page``
            Page the drilldown result and return page number *page*.
            type: `int`
        ``pagesize``
            Page the drilldown result into page of size *pagesize*.
            type: `int`
        ``order``
            Sort the result based on the dimension *sort_dimension*.
            This may be `None` (*default*) or a `list` of two-`tuples`
            where the first element is the *dimension* and the second
            element is the order (`False` for ascending, `True` for
            descending).
            Type: `list` of two-`tuples`.

        Raises:
        :exc:`ValueError`
            If a cube is not yet computed. Call :meth:`compute`
            to compute the cube.
        :exc:`KeyError`
            If a drilldown, cut or order dimension is not part of this
            cube or the order dimensions are not a subset of the drilldown
            dimensions.

        Returns: A `dict` containing the drilldown and the summary::

          {"drilldown": [
              {"num_entries": 5545,
               "amount": 41087379002.0,
               "cofog1": {"description": "",
                          "label": "Economic affairs"}},
              ... ]
           "summary": {"amount": 7353306450299.0,
                       "num_entries": 133612}}

        """
        cuts = cuts or []
        drilldowns = drilldowns or []
        order = order or []
        joins = self.alias
        fields = [db.func.sum(self.alias.c[measure]).label(measure), 
                  db.func.count(self.alias.c.id).label("entries")]
        labels = {
            # TODO: these are sqlite-specific, make a factory somewhere
            'year': db.func.strftime("%Y", self['time'].column_alias).label('year'),
            'month': db.func.strftime("%Y-%m", self['time'].column_alias).label('month'),
            }
        dimensions = set(drilldowns + [k for k,v in cuts] + [o[0] for o in order])
        for dimension in dimensions:
            if dimension in labels:
                fields.append(labels[dimension])
            else:
                joins = self[dimension.split('.')[0]].join(joins)

        group_by = []
        for key in drilldowns:
            if key in labels:
                column = labels[key]
            else:
                column = self.key(key)
                if '.' in key or column.table == self.alias:
                   fields.append(column)
                else:
                    fields.append(column.table)
            group_by.append(column)

        conditions = db.and_()
        filters = defaultdict(set)
        for key, value in cuts:
            if key in labels:
                column = labels[key]
            else:
                column = self.key(key)
            filters[column].add(value)
        for attr, values in filters.items():
            conditions.append(db.or_(*[attr==v for v in values]))

        order_by = []
        for key, direction in order:
            if key in labels:
                column = labels[key]
            else:
                column = self.key(key)
            order_by.append(column.desc() if direction else column.asc())

        query = db.select(fields, conditions, joins,
                       order_by=order_by or [measure + ' desc'],
                       group_by=group_by, use_labels=True)
        summary = {measure: 0.0, 'num_entries': 0}
        drilldown = []
        rp = self.bind.execute(query)
        while True:
            row = rp.fetchone()
            if row is None:
                break
            result = {}
            for key, value in row.items():
                if key == measure:
                    summary[measure] += value or 0
                if key == 'entries':
                    summary['num_entries'] += value or 0
                if '_' in key:
                    dimension, attribute = key.split('_', 1)
                    if dimension == 'entry':
                        result[attribute] = value
                    else:
                        if not dimension in result:
                            result[dimension] = {}

                            # TODO: backwards-compat?
                            if isinstance(self[dimension], CompoundDimension):
                                result[dimension]['taxonomy'] = \
                                        self[dimension].taxonomy
                        result[dimension][attribute] = value
                else:
                    if key == 'entries':
                        key = 'num_entries'
                    result[key] = value
            drilldown.append(result)
        offset = ((page-1)*pagesize)

        # do we really need all this:
        summary['num_drilldowns'] = len(drilldown)
        summary['page'] = page
        summary['pages'] = int(math.ceil(len(drilldown)/float(pagesize)))
        summary['pagesize'] = pagesize

        return {'drilldown': drilldown[offset:offset+pagesize],
                'summary': summary}

    def __repr__(self):
        return "<Dataset(%s:%s:%s)>" % (self.name, self.dimensions,
                self.measures)

    def __len__(self):
        rp = self.bind.execute(self.alias.count())
        return rp.fetchone()[0]

    def as_dict(self):
        return self.data.get('dataset', {})

    @classmethod
    def by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()
