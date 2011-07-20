from openspending.lib import ckan
from openspending.lib import json
from openspending.test import TestCase, helpers as h

MOCK_REGISTRY = json.load(h.fixture_file('mock_ckan.json'))

class TestCkan(TestCase):
    def setup(self):
        super(TestCkan, self).setup()
        self.patcher = h.patch('openspending.lib.ckan.CkanClient', spec=ckan.CkanClient)
        self.MockCkanClient = self.patcher.start()
        self.MockCkanClient.return_value = self.c = h.mock_ckan(MOCK_REGISTRY)

    def teardown(self):
        self.patcher.stop()
        super(TestCkan, self).teardown()

    def test_make_client(self):
        h.assert_equal(ckan.make_client(), self.c)

        self.MockCkanClient.return_value = None
        h.assert_equal(ckan.make_client(), None)

    def test_get_client(self):
        h.assert_equal(ckan.get_client(), self.c)

        # singleton now created, so this should have no effect.
        self.MockCkanClient.return_value = None
        h.assert_equal(ckan.get_client(), self.c)

    def test_package_init(self):
        p = ckan.Package('foo')
        h.assert_true(isinstance(p, ckan.Package))

    def test_package_getitem(self):
        p = ckan.Package('foo')
        h.assert_equal(p['name'], 'foo')
        h.assert_equal(p['id'], '123')

    def test_package_openspending_resource(self):
        p = ckan.Package('bar')
        h.assert_equal(p.openspending_resource('model')['id'], '123-model')
        h.assert_equal(p.openspending_resource('data')['id'], '456-data')
        h.assert_equal(p.openspending_resource('foobar'), None)

    @h.raises(ckan.AmbiguousResourceError)
    def test_package_openspending_resource_ambiguous(self):
        p = ckan.Package('baz')
        p.openspending_resource('model')

    def test_package_is_importable(self):
        p = ckan.Package
        h.assert_equal(p('foo').is_importable(), False)
        h.assert_equal(p('bar').is_importable(), True)
        h.assert_equal(p('baz').is_importable(), False)
        h.assert_equal(p('missingdata').is_importable(), False)
        h.assert_equal(p('withmapping').is_importable(), True)

    def test_metadata_for_resource(self):
        p = ckan.Package('bar')
        r = p['resources'][1]
        h.assert_equal(p.metadata_for_resource(r), {
            'currency': 'usd',
            'description': 'Notes for bar',
            'label': 'The Bar dataset',
            'name': 'bar',
            'source_description': 'Some bar data',
            'source_format': 'text/csv',
            'source_id': '456-data',
            'source_url': 'http://example.com/data.csv',
            'temporal_granularity': 'year'
        })

    def test_get_resource(self):
        p = ckan.Package('bar')
        h.assert_equal(p.get_resource('456-data')['url'], 'http://example.com/data.csv')

    @h.raises(ckan.MissingResourceError)
    def test_get_resource(self):
        p = ckan.Package('bar')
        p.get_resource('not-there')

