import json

from flask import url_for

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import load_fixture, clean_and_reindex_solr
from openspending.model.dataset import Dataset
from openspending.model.dimension import CompoundDimension


class TestDimensionController(ControllerTestCase):

    def setUp(self):
        super(TestDimensionController, self).setUp()
        load_fixture('cra')
        clean_and_reindex_solr()
        self.cra = Dataset.by_name('cra')

        for dimension in self.cra.dimensions:
            if isinstance(dimension, CompoundDimension) and \
                    dimension.name == 'cofog1':
                members = list(dimension.members(
                    dimension.alias.c.name == '3',
                    limit=1))
                self.member = members.pop()
                break

    def test_index(self):
        response = self.client.get(url_for('dimension.index', dataset='cra'))
        assert 'Paid by' in response.data, "'Paid by' not in response!"
        assert 'Paid to' in response.data, "'Paid to' not in response!"
        assert 'Programme Object Group' in response.data, \
            "'Programme Object Group' not in response!"
        assert 'CG, LG or PC' in response.data, "'CG, LG or PC' not in response!"

    def test_index_json(self):
        response = self.client.get(url_for('dimension.index', dataset='cra',
                                           format='json'))
        obj = json.loads(response.data)
        assert len(obj) == 12
        assert obj[0]['key'] == 'cap_or_cur'
        assert obj[0]['label'] == 'CG, LG or PC'

    def test_view(self):
        response = self.client.get(url_for('dimension.view', dataset='cra',
                                           dimension='from'))
        assert 'Paid by' in response.data, "'Paid by' not in response!"
        assert 'The entity that the money was paid from.' in response.data, \
            "'The entity that the money was paid from.' not in response!"

    def test_view_json(self):
        response = self.client.get(url_for('dimension.view', dataset='cra',
                                           dimension='from', format='json'))
        obj = json.loads(response.data)
        assert obj['key'] == 'from'

    def test_distinct_json(self):
        response = self.client.get(url_for('dimension.distinct', dataset='cra',
                                           dimension='from', format='json'))
        obj = json.loads(response.data)['results']
        assert len(obj) == 5, obj
        assert obj[0]['name'] == 'Dept032', obj[0]

        q = 'Ministry of Ju'
        response = self.client.get(url_for('dimension.distinct', dataset='cra',
                                           dimension='from', format='json', q=q))
        obj = json.loads(response.data)['results']
        assert len(obj) == 1, obj
        assert obj[0]['label'].startswith(q), obj[0]

    def test_view_member_html(self):
        url_ = url_for('dimension.member', dataset=self.cra.name, dimension='cofog1',
                       name=self.member['name'])
        result = self.client.get(url_)

        assert result.status == '200 OK'

        # Links to entries json and csv and entries listing
        assert '<a href="/cra/cofog1/3.json">' in result
        assert '<a href="/cra/cofog1/3/entries">Search</a>' in result

    def test_view_member_json(self):
        url_ = url_for('dimension.member', dataset=self.cra.name, dimension='cofog1',
                       name=self.member['name'], format='json')
        result = self.client.get(url_)

        assert result.status == '200 OK'
        assert result.content_type == 'application/json'

        json_data = json.loads(result.data)
        assert json_data['name'] == u'3'
        assert json_data['label'] == self.member['label']
        assert json_data['id'] == self.member['id']

    def test_view_entries_json(self):
        url_ = url_for('dimension.entries', format='json',
                       dataset=self.cra.name,
                       dimension='cofog1',
                       name=self.member['name'])
        result = self.client.get(url_)
        result = result.follow()
        assert result.status == '200 OK'
        assert result.content_type == 'application/json'

        json_data = json.loads(result.body).get('results')
        assert len(json_data) == 5

    def test_view_entries_csv(self):
        url_ = url_for('dimension.entries', format='csv',
                       dataset=self.cra.name,
                       dimension='cofog1',
                       name=self.member['name'])
        result = self.client.get(url_)
        assert result.status == '200 OK'
        assert result.content_type == 'text/csv'
        assert 'amount,' in result.data  # csv headers
        assert 'id,' in result.data  # csv headers

    def test_view_entries_html(self):
        url_ = url_for('dimension.entries', format='html',
                       dataset=self.cra.name,
                       dimension='cofog1',
                       name=self.member['name'])
        result = self.client.get(url_)
        assert result.status == '200 OK'
        assert result.content_type == 'text/html'
        # Content is filled in by client-side code.
