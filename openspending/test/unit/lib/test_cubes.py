from openspending import mongo
from openspending.test import DatabaseTestCase, helpers as h
from openspending.lib.cubes import Cube
from openspending.lib.util import deep_get

h.skip("Need to replace LoaderTestCase")

def assert_order(result, keys, expect):
    if isinstance(keys, basestring):
        keys = [keys]
    results = []
    for key in keys:
        results.append([deep_get(cell, key) for
                        cell in result['drilldown']])
    if len(results) == 1:
        result = results[0]
    else:
        result = zip(*results)
    h.assert_equal(result, expect,
                     'Not the expected order. result: %s, expected: %s' %
                     (result, expect))

class TestCube(LoaderTestCase):

    def _make_cube(self):
        loader = self._make_loader()
        loader.create_dimension('name', 'Name', '')
        loader.create_dimension('label', 'Label', '')
        loader.create_dimension('from', 'From', '')

        from_entity_a = self._make_entity(loader, name="a")
        from_entity_b = self._make_entity(loader, name="b")
        from_entity_c = self._make_entity(loader, name="c")

        to_entity_a = self._make_entity(loader, name="a")
        to_entity_b = self._make_entity(loader, name="b")
        to_entity_c = self._make_entity(loader, name="c")

        self._make_entry(loader, **{'name': '_',
                                    'from': from_entity_a,
                                    'to': to_entity_b})
        self._make_entry(loader, **{'name': '__',
                                    'from': from_entity_a,
                                    'to': to_entity_b})
        self._make_entry(loader, **{'name': '___',
                                    'from': from_entity_b,
                                    'to': to_entity_c})
        self._make_entry(loader, **{'name': '____',
                                    'from': from_entity_b,
                                    'to': to_entity_b})
        self._make_entry(loader, **{'name': '_____',
                                    'from': from_entity_c,
                                    'to': to_entity_a})
        self._make_entry(loader, **{'name': '______',
                                    'from': from_entity_c,
                                    'to': to_entity_b})

        cube = Cube.configure_default_cube(loader.dataset)
        cube.compute()
        return cube

    def test_compute_cube(self):
        cra = h.load_fixture('cra')

        cube = Cube.configure_default_cube(cra)
        cube.compute()

        h.assert_true('cubes.cra.default' in mongo.db.collection_names())

    def test_default_dimensons(self):
        # test the dimensions for a default cube.
        # We exclude 'name', 'label' and 'time'.
        # But include 'to' and 'from', 'year', and if necessary 'name'.
        cube = self._make_cube()
        h.assert_equal(sorted(cube.dimensions), ['from', 'to', 'year'])
        dataset = cube.dataset
        dataset['time_axis'] = u'time.from.month'
        new_default_cube = Cube.configure_default_cube(dataset)
        h.assert_equal(sorted(new_default_cube.dimensions),
                         ['from', 'month', 'to', 'year'])

    def test_aggregation(self):
        # Test that values are aggregated in the cube.
        cube = self._make_cube()
        collection = cube.db[cube.collection_name]
        from_a = list(collection.find({'from.name': 'a'}, as_class=dict))
        from_b = list(collection.find({'from.name': 'b'}, as_class=dict))
        h.assert_equal(len(from_a), 1)
        h.assert_equal(from_a[0]['amount'], 2000)
        h.assert_equal(len(from_b), 2)
        h.assert_equal(from_b[0]['amount'], 1000)
        h.assert_equal(from_b[1]['amount'], 1000)

    def test_fallback_for_missing_entity_name(self):
        # We use the objectid of an entity as a fallback value for 'name'
        loader = self._make_loader()
        loader.create_dimension('name', 'Name', '')
        loader.create_dimension('label', 'Label', '')
        loader.create_dimension('from', 'From', '')

        from_entity = self._make_entity(loader, name="",
                                        label='Entity w/o name')
        entry = {'name': 'Entry',
                 'label': 'Entry Label',
                 'from': from_entity,
                 'time': {'from': {'year': 2009,
                                   'day': 20090101}}}
        self._make_entry(loader, **entry)
        cube = Cube.configure_default_cube(loader.dataset)
        cube.compute()

        cube_collection = mongo.db[cube.collection_name]
        h.assert_equal(cube_collection.find().count(), 1)
        cube_from = cube_collection.find_one()['from']
        h.assert_equal(cube_from['name'], cube_from['_id'])

    def test_order(self):
        # test primary and secondary sort order
        cube = self._make_cube()

        # sort by from.name
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', False]])
        assert_order(result, 'from.name', ['a', 'b', 'b', 'c', 'c'])
        # sort by from.name (reverse)
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', True]])
        assert_order(result, 'from.name', ['c', 'c', 'b', 'b', 'a'])

        # sort by from.name and to.name
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', False], ['to.name', False]])
        assert_order(result, ['from.name', 'to.name'],
                     [('a', 'b'),
                      ('b', 'b'),
                      ('b', 'c'),
                      ('c', 'a'),
                      ('c', 'b')])

        # sort by from.name and to.name (reverse)
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', False], ['to.name', True]])
        assert_order(result, ['from.name', 'to.name'],
                     [('a', 'b'),
                      ('b', 'c'),
                      ('b', 'b'),
                      ('c', 'b'),
                      ('c', 'a')])

        # sort by from.name (reverse) and to.name
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', True], ['to.name', False]])
        assert_order(result, ['from.name', 'to.name'],
                     [('c', 'a'),
                      ('c', 'b'),
                      ('b', 'b'),
                      ('b', 'c'),
                      ('a', 'b')])

        # sort by from.name (reverse) and to.name (reverse)
        result = cube.query(drilldowns=['from', 'to'],
                            order=[['from.name', True], ['to.name', True]])
        assert_order(result, ['from.name', 'to.name'],
                     [('c', 'b'),
                      ('c', 'a'),
                      ('b', 'c'),
                      ('b', 'b'),
                      ('a', 'b')])

    def test_drilldown(self):

        def sorted_extract(drilldown):
            extracted = []
            for cell in drilldown:
                cell_extract = []
                for key in ('from.name', 'to.name', 'num_entries', 'amount'):
                    cell_extract.append(deep_get(cell, key))
                extracted.append(cell_extract)
            return sorted(extracted)

        cube = self._make_cube()
        h.assert_equal(cube.db[cube.collection_name].find().count(), 5)

        # drilldown on from and to
        result = cube.query(drilldowns=['from', 'to'])
        drilldown = result['drilldown']
        h.assert_equal(len(drilldown), 5)
        h.assert_equal(sorted_extract(drilldown),
                         [[u'a', u'b', 2, 2000.0],
                          [u'b', u'b', 1, 1000.0],
                          [u'b', u'c', 1, 1000.0],
                          [u'c', u'a', 1, 1000.0],
                          [u'c', u'b', 1, 1000.0]])

        # drilldown on from (to is not included in the drilldown)
        result = cube.query(drilldowns=['from'])
        drilldown = result['drilldown']
        h.assert_equal(len(drilldown), 3)
        h.assert_equal(sorted_extract(drilldown),
                         [[u'a', None, 2, 2000.0],
                          [u'b', None, 2, 2000.0],
                          [u'c', None, 2, 2000.0]])

        # drilldown on to (from is not included in the drilldown)
        result = cube.query(drilldowns=['to'])
        drilldown = result['drilldown']
        h.assert_equal(len(drilldown), 3)
        h.assert_equal(sorted_extract(drilldown),
                         [[None, u'a', 1, 1000.0],
                          [None, u'b', 4, 4000.0],
                          [None, u'c', 1, 1000.0]])

    def test_limit(self):
        # A limit turns a result into a paginated result with
        # the pagesize of limit

        cube = self._make_cube()
        result = cube.query(pagesize=2)

        h.assert_equal(result['summary']['pagesize'], 2)
        h.assert_equal(len(result['drilldown']), 2)
        h.assert_equal(result['summary']['page'], 1)
        h.assert_equal(result['summary']['pages'], 3)

    def test_paginate(self):
        cube = self._make_cube()

        # with pagesize < # of drilldowns
        result = cube.query(page=1, pagesize=2)
        h.assert_equal(len(result['drilldown']), 2)
        summary = result['summary']
        h.assert_equal(summary['pagesize'], 2)
        h.assert_equal(summary['page'], 1)
        h.assert_equal(summary['pages'], 3)

        # with pagesize < # of drilldowns, but page > max pages
        result = cube.query(page=5, pagesize=2)
        h.assert_equal(len(result['drilldown']), 0)
        summary = result['summary']
        h.assert_equal(summary['pagesize'], 2)
        h.assert_equal(summary['page'], 5)
        h.assert_equal(summary['pages'], 3)

        # with pagesize > # of drilldowns
        result = cube.query(page=1, pagesize=7)
        h.assert_equal(len(result['drilldown']), 5)
        summary = result['summary']
        h.assert_equal(summary['pagesize'], 7)
        h.assert_equal(summary['page'], 1)
        h.assert_equal(summary['pages'], 1)
