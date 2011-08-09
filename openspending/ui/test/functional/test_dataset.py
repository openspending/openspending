from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestDatasetController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestDatasetController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='dataset', action='index'))
        assert '''The database contains the following datasets''' in response
        assert 'cra' in response

    def test_view(self):
        response = self.app.get(url(controller='dataset', action='view', name='cra'))
        assert '''Country Regional Analysis''' in response

    def test_view_num_entries(self):
        url_ = url(controller='dataset', action='view', name='cra')
        response = self.app.get(url_)
        h.assert_true('36 entries' in response, "'36 entries' not in response!")

    def test_entries_browser(self):
        url_ = url(controller='dataset', action='entries', name='cra')
        response = self.app.get(url_)
        h.assert_true('36 entries' in response, "'36 entries' not in response!")