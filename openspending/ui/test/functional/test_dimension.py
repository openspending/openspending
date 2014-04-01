import json

from .. import ControllerTestCase, url, helpers as h
from openspending.ui.lib.helpers import member_url
from openspending.model import Dataset, CompoundDimension


class TestDimensionController(ControllerTestCase):

    def setup(self):
        super(TestDimensionController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()
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
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('Paid to' in response, "'Paid to' not in response!")
        h.assert_true(
            'Programme Object Group' in response,
            "'Programme Object Group' not in response!")
        h.assert_true(
            'CG, LG or PC' in response,
            "'CG, LG or PC' not in response!")

    def test_index_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 12)
        h.assert_equal(obj[0]['key'], 'cap_or_cur')
        h.assert_equal(obj[0]['label'], 'CG, LG or PC')

    def test_index_csv(self):
        h.skip("CSV dimension index not yet implemented!")

    def test_view(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('The entity that the money was paid from.' in response.body,
                      "'The entity that the money was paid from.' not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from',
                                    format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['key'], 'from')

    def test_distinct_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='distinct', dimension='from',
                                    format='json'))
        obj = json.loads(response.body)['results']
        assert len(obj) == 5, obj
        assert obj[0]['name'] == 'Dept032', obj[0]

        q = 'Ministry of Ju'
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='distinct', dimension='from',
                                    format='json', q=q))
        obj = json.loads(response.body)['results']
        assert len(obj) == 1, obj
        assert obj[0]['label'].startswith(q), obj[0]

    def test_view_csv(self):
        h.skip("CSV dimension view not yet implemented!")

    def test_view_member_html(self):
        url_ = member_url(self.cra.name, 'cofog1', self.member)
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')

        # Links to entries json and csv and entries listing
        h.assert_true('<a href="/cra/cofog1/3.json">' in result)
        h.assert_true('<a href="/cra/cofog1/3/entries">Search</a>' in result)

    def test_view_member_json(self):
        url_ = member_url(self.cra.name, 'cofog1', self.member, format='json')
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(json_data['name'], u'3')
        h.assert_equal(json_data['label'], self.member['label'])
        h.assert_equal(json_data['id'], self.member['id'])

    def test_view_entries_json(self):
        url_ = url(controller='dimension', action='entries', format='json',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)
        result = result.follow()
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body).get('results')
        h.assert_equal(len(json_data), 5)

    def test_view_entries_csv(self):
        url_ = url(controller='dimension', action='entries', format='csv',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)
        result = result.follow()
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/csv')
        h.assert_true('amount,' in result.body)  # csv headers
        h.assert_true('id,' in result.body)  # csv headers

    def test_view_entries_html(self):
        url_ = url(controller='dimension', action='entries', format='html',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/html')
        # Content is filled in by client-side code.
