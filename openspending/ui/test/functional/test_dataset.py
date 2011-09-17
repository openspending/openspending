import csv
import json
from StringIO import StringIO

from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestDatasetController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestDatasetController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='dataset', action='index'))
        assert 'The database contains the following datasets' in response
        assert 'cra' in response

    def test_index_json(self):
        response = self.app.get(url(controller='dataset', action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')

    def test_index_csv(self):
        response = self.app.get(url(controller='dataset', action='index', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')

    def test_view(self):
        response = self.app.get(url(controller='dataset', action='view', name='cra'))
        h.assert_true('Country Regional Analysis v2009' in response,
                      "'Country Regional Analysis v2009' not in response!")
        h.assert_true('36 entries' in response, "'36 entries' not in response!")

    def test_view_has_format_links(self):
        view_url = dict(controller='dataset', action='view', name='cra')
        response = self.app.get(url(**view_url))

        view_url.update({'format': 'json'})
        view_json_url = url(**view_url)

        view_url.update({'format': 'csv'})
        view_csv_url = url(**view_url)

        h.assert_true(view_json_url in response,
                      "Link to view page (JSON format) not in response!")
        h.assert_true(view_csv_url in response,
                      "Link to view page (CSV format) not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='dataset', action='view',
                                    name='cra', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['name'], 'cra')
        h.assert_equal(obj['label'], 'Country Regional Analysis v2009')

    def test_view_csv(self):
        response = self.app.get(url(controller='dataset', action='view',
                                    name='cra', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')

    def test_entries(self):
        response = self.app.get(url(controller='dataset', action='entries', name='cra'))
        h.assert_true('36 entries' in response, "'36 entries' not in response!")

    def test_entries_json(self):
        response = self.app.get(url(controller='dataset', action='entries',
                                    name='cra', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['facets'], {})
        h.assert_equal(obj['stats']['count'], 36)
        h.assert_equal(len(obj['results']), 20)
        h.assert_equal(obj['results'][0]['amount'], 12100000)

    def test_entries_csv(self):
        response = self.app.get(url(controller='dataset', action='entries',
                                    name='cra', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 20)
        h.assert_equal(obj[0]['amount'], '12100000')

    def test_explorer(self):
        h.skip("Not Yet Implemented!")

    def test_timeline(self):
        h.skip("Not Yet Implemented!")
