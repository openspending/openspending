"""
The ``Dataset`` serves as double function in OpenSpending: on one hand, it is
a simple domain object that can be created, modified and deleted as any other
On the other hand it serves as a controller object for the dataset-specific
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
from sqlalchemy.orm import reconstructor, relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, Boolean, DateTime
from sqlalchemy.sql.expression import false, and_, or_, select, func
from sqlalchemy.ext.associationproxy import association_proxy

from openspending.core import db
from openspending.lib.util import hash_values

from openspending.model.common import (TableHandler, MutableDict, JSONType,
                                       DatasetFacetMixin, decode_row)
from openspending.model.dimension import (CompoundDimension, DateDimension,
                                          AttributeDimension, Measure)

log = logging.getLogger(__name__)


class Dataset(TableHandler, db.Model):

    """ The dataset is the core entity of any access to data. All
    requests to the actual data store are routed through it, as well
    as data loading and model generation.

    The dataset keeps an in-memory representation of the data model
    (including all dimensions and measures) which can be used to
    generate necessary queries.
    """
    __tablename__ = 'dataset'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    label = Column(Unicode(2000))
    description = Column(Unicode())
    currency = Column(Unicode())
    default_time = Column(Unicode())
    schema_version = Column(Unicode())
    category = Column(Unicode())
    serp_title = Column(Unicode(), nullable=True)
    serp_teaser = Column(Unicode(), nullable=True)
    private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    data = Column(MutableDict.as_mutable(JSONType), default=dict)

    languages = association_proxy('_languages', 'code')
    territories = association_proxy('_territories', 'code')

    def __init__(self, data):
        self.data = data.copy()
        dataset = self.data['dataset']
        del self.data['dataset']
        self.label = dataset.get('label')
        self.name = dataset.get('name')
        self.description = dataset.get('description')
        self.currency = dataset.get('currency')
        self.category = dataset.get('category')
        self.serp_title = dataset.get('serp_title')
        self.serp_teaser = dataset.get('serp_teaser')
        self.default_time = dataset.get('default_time')
        self.languages = dataset.get('languages', [])
        self.territories = dataset.get('territories', [])
        self._load_model()

    @property
    def model(self):
        model = self.data.copy()
        model['dataset'] = self.as_dict()
        return model

    @property
    def mapping(self):
        return self.data.get('mapping', {})

    @reconstructor
    def _load_model(self):
        """ Construct the in-memory object representation of this
        dataset's dimension and measures model.

        This is called upon initialization and deserialization of
        the dataset from the SQLAlchemy store.
        """
        self.dimensions = []
        self.measures = []
        for dim, data in self.mapping.items():
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
        
        self._init_table(self.meta, self.name, 'entry',
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
                    name='fk_' + self.name + '_' + dim.name
                ))
        self._generate_table()
        self._is_generated = True

    @property
    def is_generated(self):
        if self._is_generated is None:
            self._is_generated = self.table.exists()
        return self._is_generated

    def touch(self):
        """ Update the dataset timestamp. This is used for cache
        invalidation. """
        self.updated_at = datetime.utcnow()
        db.session.add(self)

    @property
    def has_badges(self):
        """
        Property that returns True if the dataset has been given any badges
        """
        # Cast the badge count as a boolean and return it
        return bool(self.badges.count())

    def can_read(self, user):
        """
        Permissions for dataset access (read).
        Returns a boolean indicating if a user may read the dataset
        """
        # If the dataset is not private anybody can read
        # If the datset is private only users who can update it can read it
        return not self.private or self.can_update(user)

    def can_update(self, user):
        """
        Permissions for dataset updates.
        Returns a boolean indicating if a user may update the dataset
        """
        # User needs to be logged in and either admin or one of the dataset
        # managers
        return user is not None and (
            user.admin or
            db.session.query(  # Check if the user exists in managers
                self.managers.filter_by(id=user.id).exists()).first()
        )

    def can_delete(self, user):
        """
        Permissions for dataset removal (delete).
        Returns a boolean indicating if a user may delete the dataset.
        """
        # Users who can update the dataset can also delete it
        return self.can_update(user)

    def commit(self):
        pass
        # self.tx.commit()
        # self.tx = self.bind.begin()

    def _make_key(self, data):
        """ Generate a unique identifier for an entry. This is better
        than SQL auto-increment because it is stable across mutltiple
        loads and thus creates stable URIs for entries.
        """
        uniques = [self.name]
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
        dataset = self

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
            'year': dataset['time']['year'].column_alias.label('year'),
            'month': dataset['time']['yearmonth'].column_alias.label('month'),
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
                joins = dataset[dimension].join(joins)

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
                column = dataset.key(key)
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
                column = dataset.key(key)
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
                column = dataset.key(key)
            # We append the column and set the direction (True == descending)
            order_by.append(column.desc() if direction else column.asc())

        # query 1: get overall sums.
        # Here we use the stats_field we saved earlier
        query = select(stats_fields, conditions, joins)
        rp = dataset.bind.execute(query)
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
            rp = dataset.bind.execute(query)
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
        rp = dataset.bind.execute(query)

        while True:
            # Get each row in the db result and append it, decoded, to the
            # drilldown result. The decoded version is a json represenation
            row = rp.fetchone()
            if row is None:
                break
            result = decode_row(row, dataset)
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
            'currency': {m: dataset.currency for m in measures},
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

    def __repr__(self):
        return "<Dataset(%r,%r)>" % (self.id, self.name)

    def __len__(self):
        if not self.is_generated:
            return 0
        rp = self.bind.execute(self.alias.count())
        return rp.fetchone()[0]

    def as_dict(self):
        return {
            'label': self.label,
            'name': self.name,
            'description': self.description,
            'default_time': self.default_time,
            'schema_version': self.schema_version,
            'currency': self.currency,
            'category': self.category,
            'serp_title': self.serp_title,
            'serp_teaser': self.serp_teaser,
            'timestamps': {
                'created': self.created_at,
                'last_modified': self.updated_at
            },
            'languages': list(self.languages),
            'territories': list(self.territories),
            'badges': [b.as_dict(short=True) for b in self.badges]
        }

    @classmethod
    def all_by_account(cls, account):
        """ Query available datasets based on dataset visibility. """
        from openspending.model.account import Account
        criteria = [cls.private == false()]
        if account is not None and account.is_authenticated():
            criteria += ["1=1" if account.admin else "1=2",
                         cls.managers.any(Account.id == account.id)]
        q = db.session.query(cls).filter(or_(*criteria))
        q = q.order_by(cls.label.asc())
        return q

    @classmethod
    def by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()


class DatasetLanguage(db.Model, DatasetFacetMixin):
    __tablename__ = 'dataset_language'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(Dataset, backref=backref('_languages', lazy=False))

    def __init__(self, code):
        self.code = code


class DatasetTerritory(db.Model, DatasetFacetMixin):
    __tablename__ = 'dataset_territory'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(Dataset, backref=backref('_territories',
                                                    lazy=False))

    def __init__(self, code):
        self.code = code
