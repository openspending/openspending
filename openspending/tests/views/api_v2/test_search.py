from flask import url_for

from openspending.lib import json

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import (load_fixture, clean_and_reindex_solr)


class TestSearchApiController(ControllerTestCase):

    def setUp(self):
        super(TestSearchApiController, self).setUp()
        load_fixture('cra')
        clean_and_reindex_solr()

    def test_search(self):
        response = self.client.get(url_for('api_v2.search'))
        result = json.loads(response.data)

        assert result['stats']['results_count'] == 36
        assert result['stats']['results_count_query'] == 36
        assert result['facets'] == {}
        assert len(result['results']) == 36

    def test_search_results_dataset(self):
        response = self.client.get(url_for('api_v2.search'))
        result = json.loads(response.data)

        assert result['results'][0]['dataset']['name'] == 'cra'
        expected_label = 'Country Regional Analysis v2009'
        assert result['results'][0]['dataset']['label'] == expected_label

    def test_search_page_pagesize(self):
        response = self.client.get(url_for('api_v2.search', page=2, pagesize=10))
        result = json.loads(response.data)

        assert result['stats']['results_count'] == 10
        assert result['stats']['results_count_query'] == 36

    def test_search_q(self):
        response = self.client.get(url_for('api_v2.search',
                                           q="Ministry of Justice"))
        result = json.loads(response.data)

        assert result['stats']['results_count'] == 5
        assert result['stats']['results_count_query'] == 5

        id_value = '06dafa7250420ab1dc616d2bbbe310c9ad6e485e'
        assert result['results'][0]['id'] == id_value

    def test_search_filter(self):
        response = self.client.get(url_for('api_v2.search',
                                           filter="pog:P13 S091105"))
        result = json.loads(response.data)

        assert result['stats']['results_count'] == 5
        assert result['stats']['results_count_query'] == 5

        id_value = '06dafa7250420ab1dc616d2bbbe310c9ad6e485e'
        assert result['results'][0]['id'] == id_value

    def test_search_facet(self):
        response = self.client.get(url_for('api_v2.search',
                                           pagesize=0,
                                           facet_field="dataset"))
        result = json.loads(response.data)

        assert len(result['facets']['dataset']) == 1
        assert result['facets']['dataset'][0] == ['cra', 36]

    def test_search_expand_facet_dimensions(self):
        response = self.client.get(url_for('api_v2.search',
                                           dataset='cra',
                                           pagesize=0,
                                           facet_field="from|to.name",
                                           expand_facet_dimensions="1"))
        result = json.loads(response.data)

        hra = {
            "taxonomy": "from",
            "description": "",
            "id": 5,
            "name": "999",
            "label": "ENG_HRA"}

        assert result['facets']['from'][0][0] == hra
        assert result['facets']['to.name'][0][0] == 'society'

    def test_search_expand_facet_dimensions_no_dataset(self):
        response = self.client.get(url_for('api_v2.search',
                                           pagesize=0,
                                           facet_field="from",
                                           expand_facet_dimensions="1"))
        result = json.loads(response.data)

        # facets should *NOT* be expanded unless exactly 1 dataset was
        # specified
        assert result['facets']['from'][0][0] == '999'

    def test_search_order(self):
        response = self.client.get(url_for('api_v2.search',
                                           order="amount:asc"))
        result = json.loads(response.data)

        amounts = [r['amount'] for r in result['results']]
        assert amounts == sorted(amounts)

        response = self.client.get(url_for('api_v2.search',
                                           order="amount:desc"))
        result = json.loads(response.data)

        amounts = [r['amount'] for r in result['results']]
        assert amounts == sorted(amounts)[::-1]
