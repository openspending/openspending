from openspending.lib import json
from openspending.ui.lib.helpers import classifier_url

from .. import ControllerTestCase, url, helpers as h

class TestClassifierController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestClassifierController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_view_by_taxonomy_name_html(self):
        classifier = self.db['classifier'].find_one({'taxonomy': 'cofog',
                                                     'name': '03'})
        url_ = classifier_url(classifier)
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')

        # Links to entries json and csv and entries listing
        h.assert_true('<a href="/classifier/cofog/03/entries.json">'
                        in result)
        h.assert_true('<a href="/classifier/cofog/03/entries.csv">'
                        in result)
        h.assert_true('<a href="/classifier/cofog/03/entries">Search</a>'
                        in result)

        # Search box and result listing from the solr browser
        h.assert_true('class="search-form' in result)
        h.assert_equal(result.body.count('full entry'), 5)

    def test_view_by_taxonomy_name_json(self):
        classifier = self.db['classifier'].find_one({'taxonomy': 'cofog',
                                                     'name': '03'})

        url_ = classifier_url(classifier, format='json')
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(json_data['name'], u'03')
        h.assert_equal(json_data['label'], classifier['label'])
        h.assert_equal(json_data['_id'], str(classifier['_id']))

    def test_view_entries_json(self):
        classifier = self.db['classifier'].find_one({'taxonomy': 'cofog',
                                                     'name': '03'})

        url_ = url(controller='classifier', action='entries', format='json',
                   taxonomy=classifier['taxonomy'],
                   name=classifier['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(len(json_data['results']), 5)

    def test_view_entries_csv(self):
        classifier = self.db['classifier'].find_one({'taxonomy': 'cofog',
                                                     'name': '03'})

        url_ = url(controller='classifier', action='entries', format='csv',
                   taxonomy=classifier['taxonomy'],
                   name=classifier['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/csv')
        h.assert_true(result.body.startswith('_id,amount,'))  # csv headers

    def test_view_entries_html(self):
        classifier = self.db['classifier'].find_one({'taxonomy': 'cofog',
                                                     'name': '03'})

        url_ = url(controller='classifier', action='entries', format='html',
                   taxonomy=classifier['taxonomy'],
                   name=classifier['name'])
        result = self.app.get(url_)
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/html')
        h.assert_true(('<h2 class="page-title">Public order and '
                         'safety: Entries</h2>') in result)
        h.assert_equal(result.body.count('full entry'), 5)
