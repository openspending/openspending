"""
The ``Model`` serves as a controller object for the dataset-specific
data model which it represents, handling the creation, filling and migration of
the table schema associated with the dataset. As such, it holds the key set
of logic functions upon which all other queries and loading functions rely.
"""
import math
import logging
from collections import defaultdict
from datetime import datetime
from itertools import count
from sqlalchemy import ForeignKeyConstraint, MetaData
from sqlalchemy.types import Unicode
from sqlalchemy.sql.expression import and_, or_, select, func

from openspending.core import db
from openspending.lib.util import hash_values

from openspending.model.common import decode_row, TableHandler
from openspending.model.dimension import (CompoundDimension, DateDimension,
                                          AttributeDimension, Measure)

log = logging.getLogger(__name__)


class Model(TableHandler):

    def __init__(self, dataset):
        self.dataset = dataset
        self.reload()

    def reload(self):
        """ Construct the in-memory object representation of this
        dataset's dimension and measures model.

        This is called upon initialization and deserialization of
        the dataset from the SQLAlchemy store.
        """
        self.dimensions = []
        self.measures = []
        for dim, data in self.dataset.mapping.items():
            if data.get('type') == 'measure' or dim == 'amount':
                self.measures.append(Measure(self, dim, data))
                continue
            elif data.get('type') == 'date' or \
                    (dim == 'time' and data.get('datatype') == 'date'):
                dimension = DateDimension(self, dim, data)
            elif data.get('type') in ['value', 'attribute']:
                dimension = AttributeDimension(self, dim, data)
            else:
                dimension = CompoundDimension(self, dim, data)
            self.dimensions.append(dimension)
        self.init()
        self._is_generated = None

    def __getitem__(self, name):
        """ Access a field (dimension or measure) by name. """
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError()

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False

    @property
    def fields(self):
        """ Both the dimensions and metrics in this dataset. """
        return self.dimensions + self.measures

    @property
    def compounds(self):
        """ Return only compound dimensions. """
        return filter(lambda d: isinstance(d, CompoundDimension),
                      self.dimensions)

    @property
    def facet_dimensions(self):
        return [d for d in self.dimensions if d.facet]

    def init(self):
        """ Create a SQLAlchemy model for the current dataset model,
        without creating the tables and columns. This needs to be
        called both for access to the data and in order to generate
        the model physically. """
        self.bind = db.engine
        self.meta = MetaData()
        self.meta.bind = self.bind
        
        self._init_table(self.meta, self.dataset.name, 'entry',
                         id_type=Unicode(42))
        for field in self.fields:
            field.column = field.init(self.meta, self.table)
        self.alias = self.table.alias('entry')

    def generate(self):
        """ Create the tables and columns necessary for this dataset
        to keep data.
        """
        for field in self.fields:
            field.generate(self.meta, self.table)
        for dim in self.dimensions:
            if isinstance(dim, CompoundDimension):
                self.table.append_constraint(ForeignKeyConstraint(
                    [dim.name + '_id'], [dim.table.name + '.id'],
                    # use_alter=True,
                    name='fk_' + self.dataset.name + '_' + dim.name
                ))
        self._generate_table()
        self._is_generated = True

    @property
    def is_generated(self):
        if self._is_generated is None:
            self._is_generated = self.table.exists()
        return self._is_generated

    def _make_key(self, data):
        """ Generate a unique identifier for an entry. This is better
        than SQL auto-increment because it is stable across mutltiple
        loads and thus creates stable URIs for entries.
        """
        uniques = [self.dataset.name]
        for field in self.fields:
            if not field.key:
                continue
            obj = data.get(field.name)
            if isinstance(obj, dict):
                obj = obj.get('name', obj.get('id'))
            uniques.append(obj)
        return hash_values(uniques)

    def load(self, data):
        """ Handle a single entry of data in the mapping source format,
        i.e. with all needed columns. This will propagate to all dimensions
        and set values as appropriate. """
        entry = dict()
        for field in self.fields:
            field_data = data[field.name]
            entry.update(field.load(self.bind, field_data))
        entry['id'] = self._make_key(data)
        self._upsert(self.bind, entry, ['id'])

    def truncate(self):
        """ Delete all data from the dataset tables but leave the table
        structure intact.
        """
        for dimension in self.dimensions:
            dimension.truncate(self.bind)
        self._truncate(self.bind)

    def drop(self):
        """ Drop all tables created as part of this dataset, i.e. by calling
        ``generate()``. This will of course also delete the data itself.
        """
        self._drop(self.bind)
        for dimension in self.dimensions:
            dimension.drop(self.bind)
        self._is_generated = False

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
            attr_name = dimension[attr].column.name if attr else 'name'
            return dimension.alias.c[attr_name]
        return self.alias.c[dimension.column.name]

    def entries(self, conditions="1=1", order_by=None, limit=None,
                offset=0, step=10000, fields=None):
        """ Generate a fully denormalized view of the entries on this
        table. This view is nested so that each dimension will be a hash
        of its attributes.

        This is somewhat similar to the entries collection in the fully
        denormalized schema before OpenSpending 0.11 (MongoDB).
        """
        if not self.is_generated:
            return

        if fields is None:
            fields = self.fields

        joins = self.alias
        for d in self.dimensions:
            if d in fields:
                joins = d.join(joins)
        selects = [f.selectable for f in fields] + [self.alias.c.id]

        # enforce stable sorting:
        if order_by is None:
            order_by = [self.alias.c.id.asc()]

        for i in count():
            qoffset = offset + (step * i)
            qlimit = step
            if limit is not None:
                qlimit = min(limit - (step * i), step)
            if qlimit <= 0:
                break

            query = select(selects, conditions, joins, order_by=order_by,
                           use_labels=True, limit=qlimit, offset=qoffset)
            rp = self.bind.execute(query)

            first_row = True
            while True:
                row = rp.fetchone()
                if row is None:
                    if first_row:
                        return
                    break
                first_row = False
                yield decode_row(row, self)

    def aggregate(self, measures=['amount'], drilldowns=[], cuts=[],
                  page=1, pagesize=10000, order=[]):
        """ Query the dataset for a subset of cells based on cuts and
        drilldowns. It returns a structure with a list of drilldown items
        and a summary about the slice cutted by the query.

        ``measures``
            The numeric units to be aggregated over, defaults to
            [``amount``]. (type: `list`)
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
            If a cube is not yet computed. Call :meth:`compute` to compute
            the cube.
        :exc:`KeyError`
            If a drilldown, cut or order dimension is not part of this
            cube or the order dimensions are not a subset of the drilldown
            dimensions.

        Returns: A `dict` containing the drilldown and the summary: ::

          {"drilldown": [
              {"num_entries": 5545,
               "amount": 41087379002.0,
               "cofog1": {"description": "",
                          "label": "Economic affairs"}},
              ... ]
           "summary": {"amount": 7353306450299.0,
                       "num_entries": 133612}}

        """

        # Get the joins (aka alias) and the dataset
        joins = alias = self.alias
        model = self

        # Aggregation fields are all of the measures, so we create individual
        # summary fields with the sum function of SQLAlchemy
        fields = [func.sum(alias.c[m]).label(m) for m in measures]
        # We append an aggregation field that counts the number of entries
        fields.append(func.count(alias.c.id).label("entries"))
        # Create a copy of the statistics fields (for later)
        stats_fields = list(fields)

        # Create label map for time columns (year and month) for lookup
        # since they are found under the time attribute
        labels = {
            'year': model['time']['year'].column_alias.label('year'),
            'month': model['time']['yearmonth'].column_alias.label('month'),
        }

        # Get the dimensions we're interested in. These would be the drilldowns
        # and the cuts. For compound dimensions we are only interested in the
        # most significant one (e.g. for from.name we're interested in from)
        dimensions = drilldowns + [k for k, v in cuts]
        dimensions = [d.split('.')[0] for d in dimensions]

        # Loop over the dimensions as a set (to avoid multiple occurances)
        for dimension in set(dimensions):
            # If the dimension is year or month we're interested in 'time'
            if dimension in labels:
                dimension = 'time'
            # If the dimension table isn't in the automatic joins we add it
            if dimension not in [c.table.name for c in joins.columns]:
                joins = model[dimension].join(joins)

        # Drilldowns are performed using group_by SQL functions
        group_by = []
        for key in drilldowns:
            # If drilldown is in labels we append its mapped column to fields
            if key in labels:
                column = labels[key]
                group_by.append(column)
                fields.append(column)
            else:
                # Get the column from the dataset
                column = model.key(key)
                # If the drilldown is a compound dimension or the columns table
                # is in the joins we're already fetching the column so we just
                # append it to fields and the group_by
                if '.' in key or column.table == alias:
                    fields.append(column)
                    group_by.append(column)
                else:
                    # If not we add the column table to the fields and add all
                    # of that tables columns to the group_by
                    fields.append(column.table)
                    for col in column.table.columns:
                        group_by.append(col)

        # Cuts are managed using AND statements and we use a dict with set as
        # the default value to create the filters (cut on various values)
        conditions = and_()
        filters = defaultdict(set)

        for key, value in cuts:
            # If the key is in labels (year or month) we get the mapped column
            # else we get the column from the dataset
            if key in labels:
                column = labels[key]
            else:
                column = model.key(key)
            # We add the value to the set for that particular column
            filters[column].add(value)

        # Loop over the columns in the filter and add that to the conditions
        # For every value in the set we create and OR statement so we get e.g.
        # year=2007 AND (from.who == 'me' OR from.who == 'you')
        for attr, values in filters.items():
            conditions.append(or_(*[attr == v for v in values]))

        # Ordering can be set by a parameter or ordered by measures by default
        order_by = []
        # If no order is defined we default to order of the measures in the
        # order they occur (furthest to the left is most significant)
        if order is None or not len(order):
            order = [(m, True) for m in measures]

        # We loop through the order list to add the columns themselves
        for key, direction in order:
            # If it's a part of the measures we have to order by the
            # aggregated values (the sum of the measure)
            if key in measures:
                column = func.sum(alias.c[key]).label(key)
            # If it's in the labels we have to get the mapped column
            elif key in labels:
                column = labels[key]
            # ...if not we just get the column from the dataset
            else:
                column = model.key(key)
            # We append the column and set the direction (True == descending)
            order_by.append(column.desc() if direction else column.asc())

        # query 1: get overall sums.
        # Here we use the stats_field we saved earlier
        query = select(stats_fields, conditions, joins)
        rp = model.bind.execute(query)
        # Execute the query and turn them to a list so we can pop the
        # entry count and then zip the measurements and the totals together
        stats = list(rp.fetchone())
        num_entries = stats.pop()
        total = zip(measures, stats)

        # query 2: get total count of drilldowns
        if len(group_by):
            # Select 1 for each group in the group_by and count them
            query = select(['1'], conditions, joins, group_by=group_by)
            query = select([func.count('1')], '1=1', query.alias('q'))
            rp = model.bind.execute(query)
            num_drilldowns, = rp.fetchone()
        else:
            # If there are no drilldowns we still have to do one
            num_drilldowns = 1

        # The drilldown result list
        drilldown = []
        # The offset in the db, based on the page and pagesize (we have to
        # modify it since page counts starts from 1 but we count from 0
        offset = int((page - 1) * pagesize)

        # query 3: get the actual data
        query = select(fields, conditions, joins, order_by=order_by,
                       group_by=group_by, use_labels=True,
                       limit=pagesize, offset=offset)
        rp = model.bind.execute(query)

        while True:
            # Get each row in the db result and append it, decoded, to the
            # drilldown result. The decoded version is a json represenation
            row = rp.fetchone()
            if row is None:
                break
            result = decode_row(row, model)
            drilldown.append(result)

        # Create the summary based on the stats_fields and other things
        # First we add a the total for each measurement in the root of the
        # summary (watch out!) and then we add various other, self-explanatory
        # statistics such as page, number of entries. The currency value is
        # strange since it's redundant for multiple measures but is left as is
        # for backwards compatibility
        summary = {key: value for (key, value) in total}
        summary.update({
            'num_entries': num_entries,
            'currency': {m: self.dataset.currency for m in measures},
            'num_drilldowns': num_drilldowns,
            'page': page,
            'pages': int(math.ceil(num_drilldowns / float(pagesize))),
            'pagesize': pagesize
        })

        return {'drilldown': drilldown, 'summary': summary}

    def timerange(self):
        """
        Get the timerange of the dataset (based on the time attribute).
        Returns a tuple of (first timestamp, last timestamp) where timestamp
        is a datetime object
        """
        try:
            # Get the time column
            time = self.key('time')
            # We use SQL's min and max functions to get the timestamps
            query = db.session.query(func.min(time), func.max(time))
            # We just need one result to get min and max time
            return [datetime.strptime(date, '%Y-%m-%d') if date else None
                    for date in query.one()]
        except:
            return (None, None)

    def __len__(self):
        if not self.is_generated:
            return 0
        rp = self.bind.execute(self.alias.count())
        return rp.fetchone()[0]

    def __repr__(self):
        return "<Model(%r)>" % (self.dataset)
