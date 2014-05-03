from openspending.tests.base import TestCase

from openspending.lib.browser import Browser

import json
from mock import Mock, patch


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

        self.conn = Mock()
        self.dataset = Mock()
        self.dataset.name = 'mock_dataset'

        self.solr_patcher = patch('openspending.lib.browser.solr')
        mock_solr = self.solr_patcher.start()
        mock_solr.get_connection.return_value = self.conn

        self.conn.raw_query.return_value = make_response([])

        self.dataset_patcher = patch('openspending.lib.browser.Dataset')
        mock_dataset = self.dataset_patcher.start()
        mock_dataset.by_name.return_value = self.dataset

    def teardown(self):
        self.solr_patcher.stop()
        self.dataset_patcher.stop()

    def test_defaults(self):
        b = Browser()
        assert b.params['q'] == ''
        assert b.params['page'] == 1
        assert b.params['pagesize'] == 100
        assert b.params['filter'] == {}
        assert b.params['facet_field'] == []

    def test_simple_query(self):
        b = Browser()
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args

        assert solr_args['q'] == '*:*'
        assert solr_args['fq'] == []
        assert solr_args['wt'] == 'json'
        assert solr_args['fl'] == 'id, dataset'
        assert solr_args['sort'] == 'score desc, amount desc'
        assert solr_args['start'] == 0
        assert solr_args['rows'] == 100

    def test_entries_order(self):
        self.conn.raw_query.return_value = make_response([1, 2, 3])
        self.dataset.entries.return_value = make_entries([3, 1, 2])

        b = Browser()
        b.execute()
        entries = b.get_entries()

        assert map(lambda a_b: a_b[1], entries) == make_entries([1, 2, 3])

    def test_entries_stats(self):
        self.conn.raw_query.return_value = make_response([1, 2, 3])
        self.dataset.entries.return_value = make_entries([3, 1, 2])

        b = Browser()
        b.execute()
        stats = b.get_stats()

        assert stats['results_count'] == 3
        assert stats['results_count_query'] == 1234

    def test_filter(self):
        f = {'foo': 'bar', 'baz': 'with "quotes"'}
        b = Browser(filter=f)
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert '+foo:"bar"' in solr_args['fq']
        assert '+baz:"with \\"quotes\\""' in solr_args['fq']

    def test_filter_union(self):
        f = {'foo': ['bar', 'baz']}
        b = Browser(filter=f)
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert '+foo:"bar" OR +foo:"baz"' in solr_args['fq']

    def test_page_pagesize(self):
        b = Browser(page=2, pagesize=50)
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert solr_args['start'] == 50
        assert solr_args['rows'] == 50

    def test_fractional_page_pagesize(self):
        b = Browser(page=2.5, pagesize=50)
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert solr_args['start'] == 75
        assert solr_args['rows'] == 50

    def test_facets(self):
        b = Browser(facet_field=['foo', 'bar'])
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert solr_args['facet'] == 'true'
        assert solr_args['facet.mincount'] == 1
        assert solr_args['facet.sort'] == 'count'
        assert solr_args['facet.field'] == ['foo', 'bar']

    def test_facets_page_pagesize(self):
        b = Browser(facet_field=['one'], facet_page=2, facet_pagesize=50)
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert solr_args['facet.offset'] == 50
        assert solr_args['facet.limit'] == 50

    def test_order(self):
        b = Browser(order=[('amount', False), ('something.id', True)])
        b.execute()

        ignore, solr_args = self.conn.raw_query.call_args
        assert solr_args['sort'] == 'amount asc, something.id desc'
