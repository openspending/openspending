from openspending.lib import json
from openspending.ui.test import ControllerTestCase, url, helpers as h

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
                          (u'num_drilldowns', 36),
                          (u'num_entries', 36),
                          (u'page', 1),
                          (u'pages', 1),
                          (u'pagesize', 10000)])

    def test_drilldown(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', drilldown='cofog1|cofog2'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        h.assert_equal(result['summary']['num_drilldowns'], 6)
        h.assert_equal(result['summary']['amount'], -371500000.0)

    def test_cut(self):
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', cut='year:2009'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        h.assert_equal(result['summary']['num_drilldowns'], 7)
        h.assert_equal(result['summary']['amount'], 57300000.0)

    def test_order(self):
        def unique(seq):
            result = []
            for item in seq:
                if item not in result:
                    result.append(item)
            return result
        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', order='year:asc'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        order = [cell['year']  for cell in result['drilldown']]
        h.assert_equal(unique(order),
                         [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010])

        response = self.app.get(url(controller='api2', action='aggregate',
                                    dataset='cra', order='year:desc'))
        h.assert_equal(response.status, '200 OK')
        result = json.loads(response.body)
        order = [cell['year']  for cell in result['drilldown']]
        h.assert_equal(unique(order),
                         [2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003])
