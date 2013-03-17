from ... import TestCase, helpers as h

import json
from openspending.lib.browser import Browser

def make_entries(ids):
    return [{'id': id, 'dataset': 'mock_dataset'} for id in ids]

def make_response(ids):
    entries = make_entries(ids)
    return json.dumps({
        'response': {
            'numFound': 1234,
            'docs': entries
        }
    })

class TestBrowser(TestCase):
    def setup(self):
        super(TestBrowser, self).setup()

        self.conn = h.Mock()
        self.dataset = h.Mock()
        self.dataset.name = 'mock_dataset'

        self.solr_patcher = h.patch('openspending.lib.browser.solr')
        mock_solr = self.solr_patcher.start()
        mock_solr.get_connection.return_value = self.conn

        self.conn.raw_query.return_value = make_response([])

        self.model_patcher = h.patch('openspending.lib.browser.model')
        mock_model = self.model_patcher.start()
        mock_model.Dataset.by_name.return_value = self.dataset

    def teardown(self):
        self.solr_patcher.stop()
        self.model_patcher.stop()

    def test_defaults(self):
        b = Browser()
        h.assert_equal(b.params['q'], '')
        h.assert_equal(b.params['page'], 1)
        h.assert_equal(b.params['pagesize'], 100)
        h.assert_equal(b.params['filter'], {})
        h.assert_equal(b.params['facet_field'], [])

    def test_simple_query(self):
        b = Browser()
        b.execute()

        _, solr_args = self.conn.raw_query.call_args

        h.assert_equal(solr_args['q'], '*:*')
        h.assert_equal(solr_args['fq'], [])
        h.assert_equal(solr_args['wt'], 'json')
        h.assert_equal(solr_args['fl'], 'id, dataset')
        h.assert_equal(solr_args['sort'], 'score desc, amount desc')
        h.assert_equal(solr_args['start'], 0)
        h.assert_equal(solr_args['rows'], 100)

    def test_entries_order(self):
        self.conn.raw_query.return_value = make_response([1, 2, 3])
        self.dataset.entries.return_value = make_entries([3, 1, 2])

        b = Browser()
        b.execute()
        entries = b.get_entries()

        h.assert_equal(map(lambda (a, b): b, entries), make_entries([1, 2, 3]))

    def test_entries_stats(self):
        self.conn.raw_query.return_value = make_response([1, 2, 3])
        self.dataset.entries.return_value = make_entries([3, 1, 2])

        b = Browser()
        b.execute()
        stats = b.get_stats()

        h.assert_equal(stats['results_count'], 3)
        h.assert_equal(stats['results_count_query'], 1234)

    def test_filter(self):
        f = {'foo': 'bar', 'baz': 'with "quotes"'}
        b = Browser(filter=f)
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_true('+foo:"bar"' in solr_args['fq'])
        h.assert_true('+baz:"with \\"quotes\\""' in solr_args['fq'])

    def test_filter_union(self):
        f = {'foo': ['bar', 'baz']}
        b = Browser(filter=f)
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_true('+foo:"bar" OR +foo:"baz"' in solr_args['fq'])

    def test_page_pagesize(self):
        b = Browser(page=2, pagesize=50)
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_equal(solr_args['start'], 50)
        h.assert_equal(solr_args['rows'], 50)

    def test_fractional_page_pagesize(self):
        b = Browser(page=2.5, pagesize=50)
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        # Use assert_is rather than assert_equal to verify
        # that it's an integer.
        h.assert_is(solr_args['start'], 75)
        h.assert_equal(solr_args['rows'], 50)

    def test_facets(self):
        b = Browser(facet_field=['foo', 'bar'])
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_equal(solr_args['facet'], 'true')
        h.assert_equal(solr_args['facet.mincount'], 1)
        h.assert_equal(solr_args['facet.sort'], 'count')
        h.assert_equal(solr_args['facet.field'], ['foo', 'bar'])

    def test_facets_page_pagesize(self):
        b = Browser(facet_field=['one'], facet_page=2, facet_pagesize=50)
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_equal(solr_args['facet.offset'], 50)
        h.assert_equal(solr_args['facet.limit'], 50)

    def test_order(self):
        b = Browser(order=[('amount', False), ('something.id', True)])
        b.execute()

        _, solr_args = self.conn.raw_query.call_args
        h.assert_equal(solr_args['sort'], 'amount asc, something.id desc')
