import logging
import time
import sys
import math

from collections import defaultdict
from types import NoneType

from openspending import mongo
from openspending import model
from openspending.lib import util
from openspending.lib.aggregator import _aggregation_query

log = logging.getLogger(__name__)

class CubeDimensionError(Exception):
    pass

class Cube(object):
    '''A cube that preaggregates entries.

    Cubes are tied to datasets. It can be used if it is defined
    for the dataset::

      {'name': 'exampledataset',
       'cubes': {'examplecube': {'dimensions': ['dim1', 'dim2', 'dim3']}}}

    A cube contains cells for each unique combination of cube dimension
    and measures the amount (`amount`) and the number of entries
    (`num_entries`) of all entries aggregated in the cell.

    Raises: :exc:`AssertionError` if a cube with the name is not defined for
    the dataset.
    '''

    def __init__(self, dataset, cube_name):
        """
        Arguments:
        ``dataset``
            A dict-like ``dataset`` object
        ``cube_name``
            The name of the cube

        Raises: :exc:`ValueError` if the dimensions specified for the
        cube *cube_name* are not allowed for the *dataset*. See
        :meth:`_cube_dimensions`.
        """
        self.dataset = dataset
        self.name = cube_name
        self.cube_description = self._cube_description()
        self.collection_name = 'cubes.%s.%s' % (dataset['name'], cube_name)
        self.dimensions = self._cube_dimensions()
        self.db = mongo.db
        self.simpletypes = (str, unicode, int, float, NoneType)

    def compute(self):
        """
        Create the cube. This processes all entries of the dataset,
        aggregates cells based on the dimensions of the cube and
        saves them into a mongodb collection in the cubes namespace.
        """
        log.info("Computing cube '%s'...", self.name)
        log.debug(" dataset: '%s'\n  dimensions: '%s'",
                  self.dataset['name'], ', '.join(self.dimensions))
        begin = time.time()

        # query fields: We query for all fields, but handle the date
        # have to query for 'time' if dates are involved.
        # time is a required field for entries, and some datasets
        # add a dimension for time, others don't.
        # If we specify cubes, we do it with 'year' (and maybe 'month')
        query_dimensions = set(self.dimensions)

        for inval in ('_id', 'amount'):
            if inval in query_dimensions:
                raise CubeDimensionError(
                    "Not computing a cube including dimension '%s', as "
                    "no aggregations would be performed" % inval
                )

        used_time_dimensions = query_dimensions.intersection(['year', 'month'])
        additional_dimensions = []
        if used_time_dimensions:
            query_dimensions = query_dimensions - used_time_dimensions
            additional_dimensions.append('time')
        query_dimensions = query_dimensions.union(additional_dimensions)

        # remove a collection if there is one
        if self.is_computed():
            self.db.drop_collection(self.collection_name)
        collection = self.db[self.collection_name]

        def make_new_cell(cell_id):
            new_cell = {'_id': cell_id}
            for key in query_dimensions:
                # handle dates specially, collect year and month
                if key == 'time':
                    if 'year' in used_time_dimensions:
                        value = int(util.deep_get(row, 'time.from.year'))
                        new_cell['year'] = value
                    if 'month' in used_time_dimensions:
                        value = int(util.deep_get(row, 'time.from.month')[-2:])
                        new_cell['month'] = value
                    continue

                value = util.deep_get(row, key)
                if isinstance(value, dict):
                    from_day = util.deep_get(value, 'from.day')
                    if from_day:
                        new_cell[key] = row[key]
                        continue

                if isinstance(value, dict):
                    subdict = {}
                    for subkey in ('name', 'label', 'color',
                                   '_id', 'ref', 'taxonomy'):
                        if subkey in value:
                            subdict[subkey] = value[subkey]
                    if not subdict.get('name'):
                        # create a name so we can rely on it,
                        # e.g. in queries
                        subdict['name'] = subdict['_id']

                    new_cell[key] = subdict
                elif isinstance(value, self.simpletypes):
                    new_cell[key] = value
            new_cell['amount'] = row.get('amount', 0.0)
            new_cell['num_entries'] = 1
            return new_cell

        cursor = None

        try:
            cursor = _aggregation_query(self.dataset, {}, fields=list(query_dimensions))

            for row in cursor:
                cell_id = self._cell_id_for_row(row, query_dimensions)
                cell = collection.find_one({'_id': cell_id})

                if cell is None:
                    collection.insert(make_new_cell(cell_id))
                else:
                    collection.update({'_id': cell_id},
                                      {'$inc': {'amount': row.get('amount', 0.0),
                                                'num_entries': 1}})
        finally:
            del(cursor)

        self.dataset['cubes'][self.name]['num_cells'] = collection.find().count()
        model.dataset.save(self.dataset)
        log.debug("Done. Took: %ds", int(time.time() - begin))

    def query(self, drilldowns=None, cuts=None, page=1, pagesize=10000,
              order=None):
        '''
        Query the cube for a subset of cells based on cuts and drilldowns.
        It returns a structure with a list of drilldown items and
        a summary about the slice cutted by the query.

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
                          "taxonomy": "cofog",
                          "label": "Economic affairs"}},
              ... ]
           "summary": {"amount": 7353306450299.0,
                       "num_entries": 133612}}

        '''

        if not drilldowns:
            drilldowns = list(self.dimensions)
        # Assertions
        if not self.is_computed():
            raise ValueError("You have to compute the cube first")
        if not set(drilldowns) <= set(self.dimensions):
            raise KeyError((("Can't drill down on %s, allowed dimensions "
                             "are: %s") % (drilldowns, self.dimensions)))
        if order is not None:
            # extract the dimensions form the order parameter and
            # assert we get that information
            # fixme. This might go away if we sort in mongodb
            sort_dimensions = [i[0] for i in order]
            sort_dimensions = set([i.split('.')[0] for i in sort_dimensions])
            if not sort_dimensions <= set(drilldowns + ['amount']):
                raise KeyError('The dimensions in order have to be a subset '
                               'of drilldowns, but "%s" is not in drilldowns' %
                               (list(sort_dimensions - set(drilldowns))))

        summary = {'amount': 0.0,
                   'num_entries': 0}

        def _cell_key(cell):
            cell_key_values = []
            for dimension in drilldowns:
                value = cell[dimension]
                if isinstance(value, dict):
                    value = value.get('name', value.get('unparsed')) \
                            or tuple(value.items())
                cell_key_values.append(value)
            return tuple(cell_key_values)

        cursor = self.slice(cuts, drilldowns)
        summary = {'amount': 0.0, 'num_entries': 0}
        item_cells = defaultdict(list)

        for cell in cursor:
            item_cells[_cell_key(cell)].append(cell)
            summary['amount'] += cell['amount']
            summary['num_entries'] += cell['num_entries']

        items = []
        for cells in item_cells.values():
            item = {'amount': 0.0, 'num_entries': 0}
            for key in drilldowns:
                item[key] = cells[0][key]
            for cell in cells:
                item['amount'] += cell['amount']
                item['num_entries'] += cell['num_entries']
            items.append(item)

        summary['num_drilldowns'] = len(items)
        pages = math.ceil(float(len(items)) / pagesize)

        items = self._sort(items, order)
        first_item = ((page - 1) * pagesize)
        last_item = first_item + pagesize
        items = items[first_item:last_item]
        summary.update({'page': page,
                        'pages': pages,
                        'pagesize': pagesize})
        return {'drilldown': items,
                'summary': summary}

    def _sort(self, cells, order):
        '''
        sort the *cells* by one or more *order* criteria.

        ``cells``
            A list of cells
        ``order``
            See :meth:`query`

        Returns: The sorted `list` of cells
        '''
        if order is not None:
            for (dimension, direction) in reversed(order):
                key_getter = lambda cell: util.deep_get(cell, dimension)
                cells = sorted(cells, key=key_getter, reverse=direction)
        return cells

    def is_computed(self):
        '''
        Test if the cubes collection exists. If not it has to be
        computed with :meth:`compute`.
        '''
        if self.collection_name in self.db.collection_names():
            return True
        return False

    def slice(self, cuts, drilldowns):
        '''
        Cut the cube and return a slice (or dice) from it.
        This returns an iterable (a mongodb cursor). You cannot slice/dice
        the result of a slice operation again.
        '''
        cut_query = self._cut_query_spec(cuts)
        fields = drilldowns + ['amount', 'num_entries']
        return self.db[self.collection_name].find(cut_query, as_class=dict,
                                                  fields=fields)

    def _cube_description(self):
        '''
        Extract the cube description from the dataset.

        Raises: AssertionError if the cube does not exist
        Returns: A `dict` with the definition for this cube
        '''
        cubes = self.dataset.get('cubes', {})
        if self.name not in cubes:
            raise AssertionError('cube "%s" not allowed for dataset "%s"' %
                                 (self.name, self.dataset['name']))
        return cubes[self.name]

    def _cut_query_spec(self, cuts):
        '''
        Create a cut :term:`mongodb query spec` for the cuts.

        ``cuts``
            See :meth:`query`

        Raises: :exc:`KeyError` if one of the dimensions is not part of
        the cube.

        Returns: A mongodb query spec `dict`
        '''
        query_spec = {}

        if cuts is None:
            return query_spec

        for (key, value) in cuts:
            if key.split('.')[0] not in self.dimensions:
                raise KeyError(('Dimension "%s" not allowed for cube "%s" '
                                'in dataset "%s". Allowed Dimensions: %s') %
                               (key, self.name, self.dataset['name'],
                                self.dimensions))

            spec = query_spec.setdefault(key, {'$in': []})
            spec['$in'].append(value)
        return query_spec

    def _cube_dimensions(self):
        '''
        Return the dimensions of this cube.

        Raises: :exc:`ValueError` if one of the dimensions of
        for the cube does not exist as an object in the *dimension* collection
        in the database.

        Returns: A `list` of dimensions (`str`)
        '''
        cube_dimensions = set(self.cube_description['dimensions'])
        # validate against dimensions of dataset.
        dimension_objects = model.dimension.find({'dataset': self.dataset['name']})
        dimension_keys = [dimension['key'] for dimension in dimension_objects]
        possible_dimensions = set(['from', 'to', 'dataset', 'year', 'month'] +
                                  dimension_keys).difference(['name', 'label'])
        if not cube_dimensions <= possible_dimensions:
            not_existing = cube_dimensions - possible_dimensions
            raise ValueError(('These dimensions %s defined for the cube are '
                              'not allowed. Allowed dimensions: %s') %
                             (str(not_existing), str(possible_dimensions)))
        return cube_dimensions

    def _cell_id_for_row(self, row, query_dimensions):
        cell_keys = []

        for dimension in query_dimensions:
            value = util.deep_get(row, dimension)

            if isinstance(value, dict):
                from_day = util.deep_get(value, 'from.day')
                if from_day:
                    cell_keys.append(from_day)
                    cell_keys.append(util.deep_get(value, 'to.day'))
                elif '_id' in value:
                    cell_keys.append(value['_id'])
                elif 'name' in value:
                    cell_keys.append(value['name'])
            else:
                cell_keys.append(value)

        return util.hash_values(map(lambda x: unicode(x).encode('utf8'), cell_keys))

    @classmethod
    def configure_default_cube(cls, dataset):
        '''
        Configures a cube with all possible dimensions for the dataset
        *dataset* and the name 'default' and returns the cube.

        ``dataset``
            A dict-like ``dataset`` object

        Returns: A :class:`Cube` object
        '''

        dimensions = model.dimension.find({'dataset': dataset['name']})
        dimensions = [dimension['key'] for dimension in dimensions]
        dimensions.extend(['from', 'to', 'year'])
        if dataset['time_axis'] in ['time.from.month', 'time.from.day']:
            dimensions.append('month')
        # time is turned into 'year' and 'month', we don't want to aggregate
        # on name or label.
        dimensions = set(dimensions).difference(['time', 'name', 'label'])
        return cls.define_cube(dataset, 'default', dimensions)

    @classmethod
    def _validate_dimensions(cls, dimensions):
        '''
        Validate that the ``list`` *dimensions* are valid for a cube

        ``dimensions``
            list of dimension names. Type: ``list`` of ``str``

        Raises: :exc:`ValueError` if a dimension is not valid

        Returns: ``None``
        '''
        invalid = []
        if 'time' in dimensions:
            invalid.append('"time" is not a valid dimension. Specify '
                           '"year" or "year" and "month" instead')
        if invalid:
            raise ValueError('\n'.join(invalid))

    @classmethod
    def define_cube(cls, dataset, name, dimensions):
        '''
        Define a cube for the *dataset* named *name* with the given
        *dimensions*.

        Raises: :exc:`ValueError` if a dimension is not valid

        Returns: A :class:`Cube` object.
        '''
        cls._validate_dimensions(dimensions)
        dimensions = list(dimensions)
        cubes = dataset.setdefault('cubes', {})
        cubes[name] = {'dimensions': dimensions}
        return Cube(dataset, name)

    @classmethod
    def list_cubes(cls, dataset):
        cubes = dataset.setdefault('cubes', {})
        cubes_list = []
        for cube_name in cubes:
            cubes_list.append(cls(dataset, cube_name))
        return cubes_list

    @classmethod
    def update_all_cubes(cls, dataset):
        '''
        (Re)Configure the default cube and update all cubes
        for the dataset.
        '''
        cls.configure_default_cube(dataset)
        cubes = cls.list_cubes(dataset)
        for cube in cubes:
            cube.compute()


def find_cube(dataset, dimensions):
    '''
    Find a cube for the *dataset* that contains the *dimensions*.

    ``dataset``
        A dict-like ``dataset`` object
    ``dimensions``
        A `list` of dimensions

    Returns:
    A :class:`Cube` object if a fitting cube is found or `None` if no
    cube is found. The returned cube may not be computed yet (see
    :meth:`is_computed`.
    '''
    cubes = dataset.get('cubes', {})
    dimensions = set(dimensions)
    cube = None
    # sort the cubes by the number of cells (smaller == faster) and
    # sort the not computed cubes to the end.
    cubes = sorted(cubes.items(),
                   key=lambda cube: cube[1].get('num_cells', sys.maxint))
    for (name, description) in cubes:
        if dimensions <= set(description['dimensions']):
            cube = Cube(dataset, name)
            if cube.is_computed():
                break
    return cube
