from flask import url_for

from openspending.lib import json

from csv import DictReader
from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import load_fixture


class TestSearchApiController(ControllerTestCase):

    def setUp(self):
        super(TestSearchApiController, self).setUp()
        load_fixture('cra')
        # clean_and_reindex_solr()

    def test_aggregate(self):
        response = self.client.get(url_for('api_v2.aggregate', dataset='cra'))
        assert '200' in response.status
        assert 'application/json' in response.content_type
        result = json.loads(response.data)
        assert sorted(result.keys()) == [u'drilldown', u'summary'], result

        result['summary'].pop("cache_key", None)
        result['summary'].pop("cached", None)
        expected_result = [(u'amount', -371500000.0),
                           (u'currency', {u'amount': u'GBP'}),
                           (u'num_drilldowns', 1),
                           (u'num_entries', 36),
                           (u'page', 1),
                           (u'pages', 1),
                           (u'pagesize', 10000)]
        assert sorted(result['summary'].items()) == expected_result

    def test_aggregate_drilldown(self):
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra',
                                           drilldown='cofog1|cofog2'))
        assert '200' in response.status

        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 6
        assert result['summary']['amount'] == -371500000.0

    def test_aggregate_drilldown_format_csv(self):
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra',
                                           drilldown='cofog1|cofog2',
                                           format='csv'))
        assert '200' in response.status
        result = list(DictReader(response.data.split('\n')))
        assert len(result) == 6
        assert result[0]['cofog2.name'] == '10.1', result[0]

    def test_aggregate_measures(self):
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', cut='year:2009',
                                           measure='total'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 1, result['summary']
        assert result['summary']['total'] == 57300000.0, result['summary']

    def test_aggregate_multiple_measures(self):
        """
        Test whether multiple measures work. Multiple measures are
        separated with | in the measure url parameter.
        """

        # Get the aggregated amount and total values for year 2009
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', cut='year:2009',
                                           measure='amount|total'))

        # This should return a status code 200.
        assert '200' in response.status, \
            'Aggregation for multiple measures did not return successfully'

        # Load the json body into a dict
        result = json.loads(response.data)

        # Only one drilldown should be made even if there are two measures
        assert result['summary']['num_drilldowns'] == 1, \
            "Aggregation of multiple measures wasn't done with one drilldown"

        # Since amount measure and total measure are two different measures
        # for the same field in the csv file they should contain the same
        # amount but still be distinct.
        assert result['summary']['total'] == 57300000.0, \
            'Multiple measure aggregation of total measure is not correct'
        assert result['summary']['amount'] == 57300000.0, \
            'Multiple measure aggregation of amount measure is not correct'

    def test_aggregate_cut(self):
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', cut='year:2009'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 1, result['summary']
        assert result['summary']['amount'] == 57300000.0, result['summary']

    def test_aggregate_order(self):
        def unique(seq):
            result = []
            for item in seq:
                if item not in result:
                    result.append(item)
            return result
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', order='year:asc',
                                           drilldown='year'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        order = [cell['time']['year'] for cell in result['drilldown']]
        expected_result = map(unicode, [2003, 2004, 2005, 2006, 2007,
                                        2008, 2009, 2010])
        assert unique(order) == expected_result

        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', order='year:desc',
                                           drilldown='year'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        order = [cell['time']['year'] for cell in result['drilldown']]
        expected_result = map(unicode, [2010, 2009, 2008, 2007, 2006,
                                        2005, 2004, 2003])
        assert unique(order) == expected_result

    def test_inflation(self):
        """
        Test for inflation support in the aggregation api. Inflation works
        by adding a url parameter containing the target year of inflation.

        This test has hard coded values based on existing inflation data used
        by an external module. This may therefore need updating should the
        inflation data become more accurate with better data.
        """

        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', cut='year:2009',
                                           inflate='2011'))
        assert '200' in response.status, \
            "Inflation request didn't return successfully (status isn't 200)"

        result = json.loads(response.data)

        # Check for inflated amount
        assert 'amount' in result['summary'], \
            "Amount is absent for the result summary"
        assert int(result['summary']['amount']) == 61836609, \
            "Inflation amount is incorrect"

        # Check for original amount
        assert 'original' in result['summary'], \
            "Original amount not in inflation request"
        assert result['summary']['original'] == 57300000.0, \
            "Original amount (for inflation) is incorrect"

        # Check for inflation adjustment object in drilldown results
        assert len(result['drilldown']) == 1, \
            "Drilldown results were not of length 1"
        assert 'inflation_adjustment' in result['drilldown'][0], \
            "Inflation adjustment is not present in drilldown results"

        # Check for what happens when inflation is not possible
        response = self.client.get(url_for('api_v2.aggregate',
                                           dataset='cra', cut='year:2009',
                                           inflate='1000'))
        assert '200' in response.status, \
            "Incorrect inflation did not return sucessfully (status isn't 200)"

        result = json.loads(response.data)

        assert 'warning' in result, \
            "No warning given when inflation not possible"
        assert result['summary']['amount'] == 57300000.0, \
            "Amount does not fall back to the original amount"
