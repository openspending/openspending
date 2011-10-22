from openspending.lib import json
from openspending.ui.lib.helpers import classifier_url
from openspending.model import Dataset, CompoundDimension, meta as db

from .. import ControllerTestCase, url, helpers as h

class TestClassifierController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestClassifierController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()
        self.cra = Dataset.by_name('cra')
        for dimension in self.cra.dimensions:
            if isinstance(dimension, CompoundDimension) and \
                    dimension.taxonomy == 'cofog':
                members = list(dimension.members(
                    dimension.alias.c.name=='3',
                    limit=1))
                self.classifier = members.pop()
                break

    def test_view_by_taxonomy_name_html(self):
        url_ = classifier_url(self.cra.name, self.classifier)
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')

        # Links to entries json and csv and entries listing
        h.assert_true('<a href="/cra/cofog/3.json">'
                        in result)
        h.assert_true('<a href="/cra/cofog/3/entries">Search</a>'
                        in result)

    def test_view_by_taxonomy_name_json(self):
        url_ = classifier_url(self.cra.name, self.classifier, format='json')
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(json_data['name'], u'3')
        h.assert_equal(json_data['label'], self.classifier['label'])
        h.assert_equal(json_data['id'], self.classifier['id'])

    def test_view_entries_json(self):
        url_ = url(controller='classifier', action='entries', format='json',
                   dataset=self.cra.name,
                   taxonomy=self.classifier['taxonomy'],
                   name=self.classifier['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(len(json_data['results']), 5)

    def test_view_entries_csv(self):
        url_ = url(controller='classifier', action='entries', format='csv',
                   dataset=self.cra.name,
                   taxonomy=self.classifier['taxonomy'],
                   name=self.classifier['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/csv')
        h.assert_true('amount,' in result.body)  # csv headers
        h.assert_true('id,' in result.body)  # csv headers

    def test_view_entries_html(self):
        url_ = url(controller='classifier', action='entries', format='html',
                   dataset=self.cra.name,
                   taxonomy=self.classifier['taxonomy'],
                   name=self.classifier['name'])
        result = self.app.get(url_)
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/html')
        h.assert_true(('Public order and safety') in result)
        h.assert_true(('financial transactions') in result)
        h.assert_equal(result.body.count('details'), 5)
