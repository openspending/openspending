from openspending.test import DatabaseTestCase, helpers as h
from openspending.lib import solr_util as solr

class TestSearch(DatabaseTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestSearch, self).setup()
        h.load_fixture('cra')

        ourdict = {
            '_id': 'myspecialid',
            'cofog1_ws': 'foobar'
        }

        self.solr = solr.get_connection()
        self.solr.add(**ourdict)
        self.solr.commit()

        solr.build_index(dataset_name='cra')

    def test_search(self):
        q = 'cofog1_ws:foobar'
        query = self.solr.query(q, rows=10, sort='score desc, amount desc')
        assert query.numFound == 1, query.numFound

    def test_search_load(self):
        q = 'pensions'
        query = self.solr.query(q, rows=10, sort='score desc, amount desc')
        assert query.numFound == 8, query.numFound

    def test_search_load_time(self):
        q = 'time.from.year:2008'
        query = self.solr.query(q, rows=10)
        assert query.numFound == 6, query.numFound

        q = 'time.from.parsed:[2008-01-01T00:00:00Z TO 2008-01-02T00:00:00Z]'
        query = self.solr.query(q, rows=10)
        assert query.numFound == 6, query.numFound

    def test_stats(self):
        q = '*:*'
        query = self.solr.query(q, stats='true', stats_field='amount',
                                stats_facet='time.from.year', rows=0)
        amount = query.stats['stats_fields']['amount']
        timeamount = amount['facets']['time.from.year']['2007']
        assert timeamount['sum'] == -20300000.0, timeamount['sum']
        assert timeamount['mean'] == -4060000.0, timeamount['mean']
