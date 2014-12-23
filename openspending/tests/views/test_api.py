from flask import url_for

from openspending.lib import json
from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.model.account import Account

from csv import DictReader
from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import (make_account, load_fixture,
                                        clean_and_reindex_solr)


class TestApiController(ControllerTestCase):

    def setUp(self):
        super(TestApiController, self).setUp()
        load_fixture('cra')
        clean_and_reindex_solr()

    def test_aggregate(self):
        response = self.client.get(url_for('api.aggregate', dataset='cra'))
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
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra',
                                           drilldown='cofog1|cofog2'))
        assert '200' in response.status

        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 6
        assert result['summary']['amount'] == -371500000.0

    def test_aggregate_drilldown_format_csv(self):
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra',
                                           drilldown='cofog1|cofog2',
                                           format='csv'))
        assert '200' in response.status
        result = list(DictReader(response.data.split('\n')))
        assert len(result) == 6
        assert result[0]['cofog2.name'] == '10.1'

    def test_aggregate_measures(self):
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra', cut='year:2009',
                                           measure='total'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 1
        assert result['summary']['total'] == 57300000.0

    def test_aggregate_multiple_measures(self):
        """
        Test whether multiple measures work. Multiple measures are
        separated with | in the measure url parameter.
        """

        # Get the aggregated amount and total values for year 2009
        response = self.client.get(url_for('api.aggregate',
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
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra', cut='year:2009'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        assert result['summary']['num_drilldowns'] == 1
        assert result['summary']['amount'] == 57300000.0

    def test_aggregate_order(self):
        def unique(seq):
            result = []
            for item in seq:
                if item not in result:
                    result.append(item)
            return result
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra', order='year:asc',
                                           drilldown='year'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        order = [cell['year'] for cell in result['drilldown']]
        expected_result = map(unicode, [2003, 2004, 2005, 2006, 2007,
                                        2008, 2009, 2010])
        assert unique(order) == expected_result

        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra', order='year:desc',
                                           drilldown='year'))
        assert response.status == '200 OK'
        result = json.loads(response.data)
        order = [cell['year'] for cell in result['drilldown']]
        expected_result = map(unicode, [2010, 2009, 2008, 2007, 2006,
                                        2005, 2004, 2003])
        assert unique(order) == expected_result

    # def test_search(self):
    #     response = self.client.get(url_for('api.search'))
    #     result = json.loads(response.data)

    #     assert result['stats']['results_count'] == 36
    #     assert result['stats']['results_count_query'] == 36
    #     assert result['facets'] == {}
    #     assert len(result['results']) == 36

    # def test_search_results_dataset(self):
    #     response = self.client.get(url_for('api.search'))
    #     result = json.loads(response.data)

    #     assert result['results'][0]['dataset']['name'] == 'cra'
    #     expected_label = 'Country Regional Analysis v2009'
    #     assert result['results'][0]['dataset']['label'] == expected_label

    # def test_search_page_pagesize(self):
    #     response = self.client.get(url_for('api.search', page=2, pagesize=10))
    #     result = json.loads(response.data)

    #     assert result['stats']['results_count'] == 10
    #     assert result['stats']['results_count_query'] == 36

    # def test_search_q(self):
    #     response = self.client.get(url_for('api.search',
    #                                        q="Ministry of Justice"))
    #     result = json.loads(response.data)

    #     assert result['stats']['results_count'] == 5
    #     assert result['stats']['results_count_query'] == 5

    #     id_value = '06dafa7250420ab1dc616d2bbbe310c9ad6e485e'
    #     assert result['results'][0]['id'] == id_value

    # def test_search_filter(self):
    #     response = self.client.get(url_for('api.search',
    #                                        filter="pog:P13 S091105"))
    #     result = json.loads(response.data)

    #     assert result['stats']['results_count'] == 5
    #     assert result['stats']['results_count_query'] == 5

    #     id_value = '06dafa7250420ab1dc616d2bbbe310c9ad6e485e'
    #     assert result['results'][0]['id'] == id_value

    # def test_search_facet(self):
    #     response = self.client.get(url_for('api.search',
    #                                        pagesize=0,
    #                                        facet_field="dataset"))
    #     result = json.loads(response.data)

    #     assert len(result['facets']['dataset']) == 1
    #     assert result['facets']['dataset'][0] == ['cra', 36]

    # def test_search_expand_facet_dimensions(self):
    #     response = self.client.get(url_for('api.search',
    #                                        dataset='cra',
    #                                        pagesize=0,
    #                                        facet_field="from|to.name",
    #                                        expand_facet_dimensions="1"))
    #     result = json.loads(response.data)

    #     hra = {
    #         "taxonomy": "from",
    #         "description": "",
    #         "id": 5,
    #         "name": "999",
    #         "label": "ENG_HRA"}

    #     assert result['facets']['from'][0][0] == hra
    #     assert result['facets']['to.name'][0][0] == 'society'

    # def test_search_expand_facet_dimensions_no_dataset(self):
    #     response = self.client.get(url_for('api.search',
    #                                        pagesize=0,
    #                                        facet_field="from",
    #                                        expand_facet_dimensions="1"))
    #     result = json.loads(response.data)

    #     # facets should *NOT* be expanded unless exactly 1 dataset was
    #     # specified
    #     assert result['facets']['from'][0][0] == '999'

    # def test_search_order(self):
    #     response = self.client.get(url_for('api.search',
    #                                        order="amount:asc"))
    #     result = json.loads(response.data)

    #     amounts = [r['amount'] for r in result['results']]
    #     assert amounts == sorted(amounts)

    #     response = self.client.get(url_for('api.search',
    #                                        order="amount:desc"))
    #     result = json.loads(response.data)

    #     amounts = [r['amount'] for r in result['results']]
    #     assert amounts == sorted(amounts)[::-1]

    def test_inflation(self):
        """
        Test for inflation support in the aggregation api. Inflation works
        by adding a url parameter containing the target year of inflation.

        This test has hard coded values based on existing inflation data used
        by an external module. This may therefore need updating should the
        inflation data become more accurate with better data.
        """

        response = self.client.get(url_for('api.aggregate',
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
        response = self.client.get(url_for('api.aggregate',
                                           dataset='cra', cut='year:2009',
                                           inflate='1000'))
        assert '200' in response.status, \
            "Incorrect inflation did not return sucessfully (status isn't 200)"

        result = json.loads(response.data)

        assert 'warning' in result, \
            "No warning given when inflation not possible"
        assert result['summary']['amount'] == 57300000.0, \
            "Amount does not fall back to the original amount"

    def test_permissions(self):
        """
        Test permissions API which tells users if they are allowed to
        perform CRUD operations on a given dataset
        """

        # Create our users
        admin = make_account('test_admin', admin=True)
        maintainer = make_account('maintainer')
        user = make_account('test_user')

        # Set maintainer as maintainer of cra dataset
        dataset = Dataset.by_name('cra')
        dataset.managers.append(maintainer)
        db.session.add(dataset)
        db.session.commit()

        # Make the url reusable
        permission = url_for('api.permissions')

        # First we try to get permissions without dataset parameter
        # This should return a 200 but include an error message and nothing
        # else
        response = self.client.get(permission)
        json_response = json.loads(response.data)
        assert len(json_response.keys()) == 1, \
            'Parameterless call response includes more than one properties'
        assert 'error' in json_response, \
            'Error property not present in parameterless call response'

        # Dataset is public by default

        # Anonymous user
        response = self.client.get(permission, query_string={'dataset': 'cra'})
        anon_response = json.loads(response.data)
        assert not anon_response['create'], \
            'Anonymous user can create existing dataset'
        assert anon_response['read'], \
            'Anonymous user cannot read public dataset'
        assert not anon_response['update'], \
            'Anonymous user can update existing dataset'
        assert not anon_response['delete'], \
            'Anonymous user can delete existing dataset'
        # Normal user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert anon_response == normal_response, \
            'Normal user has wrong permissions for a public dataset'
        # Maintainer
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': maintainer.api_key})
        main_response = json.loads(response.data)
        assert not main_response['create'], \
            'Maintainer can create a dataset with an existing (public) name'
        assert main_response['read'], \
            'Maintainer is not able to read public dataset'
        assert main_response['update'], \
            'Maintainer is not able to update public dataset'
        assert main_response['delete'], \
            'Maintainer is not able to delete public dataset'
        # Administrator
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': admin.api_key})
        admin_response = json.loads(response.data)
        # Permissions for admins should be the same as for maintainer
        assert main_response == admin_response, \
            'Admin and maintainer permissions differ on public datasets'

        # Set cra dataset as private so only maintainer and admin should be
        # able to 'read' (and 'update' and 'delete'). All others should get
        # False on everything
        dataset = Dataset.by_name('cra')
        dataset.private = True
        db.session.add(dataset)
        db.session.commit()

        # Anonymous user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra'})
        anon_response = json.loads(response.data)
        assert True not in anon_response.values(), \
            'Anonymous user has access to a private dataset'
        # Normal user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert anon_response == normal_response, \
            'Normal user has access to a private dataset'
        # Maintainer
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': maintainer.api_key})
        main_response = json.loads(response.data)
        assert not main_response['create'], \
            'Maintainer can create a dataset with an existing (private) name'
        assert main_response['read'], \
            'Maintainer is not able to read private dataset'
        assert main_response['update'], \
            'Maintainer is not able to update private dataset'
        assert main_response['delete'], \
            'Maintainer is not able to delete private dataset'
        # Administrator
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': admin.api_key})
        admin_response = json.loads(response.data)
        # Permissions for admins should be the same as for maintainer
        assert main_response == admin_response, \
            'Admin does not have the same permissions as maintainer'

        # Now we try accessing a nonexistent dataset
        # Everyone except anonymous user should have the same permissions
        # We don't need to check with maintainer or admin now since this
        # applies to all logged in users
        response = self.client.get(permission,
                                   query_string={'dataset': 'nonexistent'})
        anon_response = json.loads(response.data)
        assert True not in anon_response.values(), \
            'Anonymous users has permissions on a nonexistent datasets'
        # Any logged in user (we use normal user)
        response = self.client.get(permission,
                                   query_string={'dataset': 'nonexistent',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert normal_response['create'], \
            'User cannot create a nonexistent dataset'
        assert not normal_response['read'], \
            'User can read a nonexistent dataset'
        assert not normal_response['update'], \
            'User can update a nonexistent dataset'
        assert not normal_response['delete'], \
            'User can delete a nonexistent dataset'


#class TestApiNewDataset(ControllerTestCase):
class cccc(object):

    """
    This checks for authentication with a header api key while also
    testing for loading of data via the api
    """

    def setUp(self):
        super(TestApiNewDataset, self).setUp()
        self.user = make_account('test_new')

        self.user2 = make_account('test_new2')

    def test_new_dataset(self):
        user = Account.by_name('test_new')

        u = url_for('api.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert "200" in response.status
        dataset = Dataset.by_name('openspending-example')
        assert dataset is not None
        assert dataset.private is False

    def test_private_dataset(self):
        user = Account.by_name('test_new')

        u = url_for('api.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'private': 'true'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert "200" in response.status
        dataset = Dataset.by_name('openspending-example')
        assert dataset is not None
        assert dataset.private is True

    def test_new_no_apikey(self):
        u = url_for('api.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params)
        assert "403" in response.status
        assert Dataset.by_name('openspending-example') is None

    def test_new_wrong_user(self):
        # First we add a Dataset with user 'test_new'
        user = Account.by_name('test_new')
        
        u = url_for('api.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})

        assert "200" in response.status
        assert Dataset.by_name('openspending-example') is not None

        # After that we try to update the Dataset with user 'test_new2'
        user = Account.by_name('test_new2')
        
        u = url_for('api.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert '403' in response.status
