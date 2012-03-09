from openspending.lib import json
from .. import ControllerTestCase, url, helpers as h

class TestApi2Controller(ControllerTestCase):
    def setup(self):
        super(TestApi2Controller, self).setup()
        h.load_fixture('cra')

    def test_aggregate(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra'))
        h.assert_equal(response.status, '200 OK')
        h.assert_equal(response.content_type, 'application/json')
        result = json.loads(response.body)
        h.assert_equal(sorted(result.keys()), [u'drilldown', u'summary'])
        h.assert_equal(sorted(result['summary'].items()),
                         [(u'amount', -371500000.0),
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
