from openspending.lib import json
from csv import DictReader
from .. import ControllerTestCase, url, helpers as h

class TestApi2Controller(ControllerTestCase):
    def setup(self):
        super(TestApi2Controller, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_aggregate(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra'))
        h.assert_equal(response.status, '200 OK')
        h.assert_equal(response.content_type, 'application/json')
        result = json.loads(response.body)
        h.assert_equal(sorted(result.keys()), [u'drilldown', u'summary'])
        h.assert_equal(sorted(result['summary'].items()),
                         [(u'amount', -371500000.0),
                          (u'currency', {u'amount': u'GBP'}),
                          (u'num_drilldowns', 1),
                          (u'num_entries', 36),
                          (u'page', 1),
                          (u'pages', 1),
                          (u'pagesize', 10000)])

    def test_aggregate_drilldown(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', drilldown='cofog1|cofog2'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        h.assert_equal(result['summary']['num_drilldowns'], 6)
        h.assert_equal(result['summary']['amount'], -371500000.0)

    def test_aggregate_drilldown_format_csv(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', drilldown='cofog1|cofog2',
                                    format='csv'))
        h.assert_equal(response.status, '200 OK')
        result = DictReader(response.body)
        print result

    def test_aggregate_measures(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', cut='year:2009',
                                    measure='total'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        h.assert_equal(result['summary']['num_drilldowns'], 1)
        h.assert_equal(result['summary']['total'], 57300000.0)

    def test_aggregate_cut(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', cut='year:2009'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        h.assert_equal(result['summary']['num_drilldowns'], 1)
        h.assert_equal(result['summary']['amount'], 57300000.0)

    def test_aggregate_order(self):
        def unique(seq):
            result = []
            for item in seq:
                if item not in result:
                    result.append(item)
            return result
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', order='year:asc',
                                    drilldown='year'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        order = [cell['year']  for cell in result['drilldown']]
        h.assert_equal(unique(order),
                         map(unicode, [2003, 2004, 2005, 2006, 2007, 2008, 2009,
                             2010]))

        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', order='year:desc',
                                    drilldown='year'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        order = [cell['year']  for cell in result['drilldown']]
        h.assert_equal(unique(order),
                         map(unicode, [2010, 2009, 2008, 2007, 2006, 2005, 2004,
                             2003]))

    def test_search(self):
        response = self.app.get(url(controller='api2', action='search'))
        result = json.loads(response.body)

        h.assert_equal(result['stats']['results_count'], 36)
        h.assert_equal(result['stats']['results_count_query'], 36)
        h.assert_equal(result['facets'], {})
        h.assert_equal(len(result['results']), 36)

    def test_search_page_pagesize(self):
        response = self.app.get(url(controller='api2', action='search', page=2, pagesize=10))
        result = json.loads(response.body)

        h.assert_equal(result['stats']['results_count'], 10)
        h.assert_equal(result['stats']['results_count_query'], 36)

    def test_search_q(self):
        response = self.app.get(url(controller='api2', action='search', q="Ministry of Justice"))
        result = json.loads(response.body)

        h.assert_equal(result['stats']['results_count'], 5)
        h.assert_equal(result['stats']['results_count_query'], 5)
        h.assert_equal(result['results'][0]['id'], "06dafa7250420ab1dc616d2bbbe310c9ad6e485e")

    def test_search_filter(self):
        response = self.app.get(url(controller='api2', action='search', filter="pog:P13 S091105"))
        result = json.loads(response.body)

        h.assert_equal(result['stats']['results_count'], 5)
        h.assert_equal(result['stats']['results_count_query'], 5)
        h.assert_equal(result['results'][0]['id'], "06dafa7250420ab1dc616d2bbbe310c9ad6e485e")

    def test_search_facet(self):
        response = self.app.get(url(controller='api2', action='search', pagesize=0, facet_field="dataset"))
        result = json.loads(response.body)

        h.assert_equal(len(result['facets']['dataset']), 1)
        h.assert_equal(result['facets']['dataset'][0], ['cra', 36])

    def test_search_expand_facet_dimensions(self):
        response = self.app.get(url(controller='api2',
                                    action='search',
                                    dataset='cra',
                                    pagesize=0,
                                    facet_field="from|to.name",
                                    expand_facet_dimensions="1"))
        result = json.loads(response.body)

        hra = {"taxonomy": "from", "description": "", "id": 5, "name": "999", "label": "ENG_HRA"}

        h.assert_equal(result['facets']['from'][0][0], hra)
        h.assert_equal(result['facets']['to.name'][0][0], 'society')

    def test_search_expand_facet_dimensions_no_dataset(self):
        response = self.app.get(url(controller='api2',
                                    action='search',
                                    pagesize=0,
                                    facet_field="from",
                                    expand_facet_dimensions="1"))
        result = json.loads(response.body)

        # facets should *NOT* be expanded unless exactly 1 dataset was specified
        h.assert_equal(result['facets']['from'][0][0], '999')

    def test_search_order(self):
        response = self.app.get(url(controller='api2', action='search', order="amount:asc"))
        result = json.loads(response.body)

        amounts = [r['amount'] for r in result['results']]

        h.assert_equal(amounts, sorted(amounts))

        response = self.app.get(url(controller='api2', action='search', order="amount:desc"))
        result = json.loads(response.body)

        amounts = [r['amount'] for r in result['results']]

        h.assert_equal(amounts, sorted(amounts)[::-1])
