# coding: UTF-8
from datetime import datetime
from openspending.lib import solr_util as solr

from openspending.tests.base import TestCase
from nose.tools import assert_raises
from mock import Mock, patch


class TestSolrUtil(TestCase):

    def setup(self):
        super(TestSolrUtil, self).setup()
        reload(solr)
        self.patcher = patch('openspending.lib.solr_util.SolrConnection')
        self.mock_solr = self.patcher.start()

    def teardown(self):
        self.patcher.stop()
        super(TestSolrUtil, self).teardown()

    def test_configure_defaults(self):
        solr.configure()

        assert solr.url == 'http://localhost:8983/solr'
        assert solr.http_user is None
        assert solr.http_pass is None

    def test_configure(self):
        config = Mock()
        config.get.side_effect = ['myurl', 'myuser', 'mypass']
        solr.configure(config)

        assert solr.url == 'myurl'
        assert solr.http_user == 'myuser'
        assert solr.http_pass == 'mypass'

    def test_get_connection(self):
        conn = solr.get_connection()
        conn = solr.get_connection()
        self.mock_solr.assert_called_once_with(
            'http://localhost:8983/solr',
            http_user=None,
            http_pass=None)
        assert conn == self.mock_solr.return_value

    def test_drop_index(self):
        solr.drop_index('foo')
        self.mock_solr.return_value.delete_query.assert_called_once_with(
            'dataset:foo')
        self.mock_solr.return_value.commit.assert_called_once()

    def test_dataset_entries(self):
        self.mock_solr.return_value.raw_query.return_value = \
            '{"response":{"numFound":42}}'
        assert solr.dataset_entries('foo') == 42

    def test_extend_entry(self):
        dataset = Mock()
        dataset.id = 123
        dataset.name = 'mydataset'

        now = datetime.now()

        entry = {
            'id': 456,
            'time': now,
            'foo.name': 'uber',
            'foo.label': 'UberLabel',
            'foo.tags': ['one', 'two', 'three']
        }

        expected = {
            '_id': 'mydataset::456',
            'id': 456,
            'time': datetime(now.year, now.month, now.day, now.hour,
                             now.minute, now.second, 0, solr.UTC()),
            'dataset.id': 123,
            'dataset': 'mydataset',
            'foo.name': u'uber',
            'foo': u'uber',
            'foo.label': 'UberLabel',
            'foo.label_facet': 'UberLabel',
            'foo.tags': 'one two three'
        }

        res = solr.extend_entry(entry, dataset)
        assert res == expected

    @patch('openspending.lib.solr_util.model.Dataset')
    def test_build_index_no_dataset(self, mock_ds):
        mock_ds.by_name.return_value = None
        assert_raises(ValueError, solr.build_index, 'foobar')

    @patch('openspending.lib.solr_util.model.Dataset')
    @patch('openspending.lib.solr_util.extend_entry')
    def test_build_index(self, mock_ee, mock_ds):
        ds = mock_ds.by_name.return_value
        ds.entries.return_value = [{'foo': 123}, {'foo': 456}, {'foo': 789}]

        mock_ee.side_effect = lambda e, d: e['foo']

        solr.build_index('mydataset')
        conn = self.mock_solr.return_value
        conn.add_many.assert_called_once_with([123, 456, 789])
        conn.commit.assert_called_once()

    @patch('openspending.lib.solr_util.model.Dataset')
    @patch('openspending.lib.solr_util.extend_entry')
    def test_build_index_batch(self, mock_ee, mock_ds):
        ds = mock_ds.by_name.return_value
        ds.entries.return_value = [{'foo': 'bar'}] * 2500

        solr.build_index('mydataset')
        conn = self.mock_solr.return_value
        assert conn.add_many.call_count == 3
        assert conn.commit.call_count == 3
