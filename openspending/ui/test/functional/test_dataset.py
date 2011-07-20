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
        response = self.app.get(url(controller='dataset', action='view', id='cra'))
        assert '''Country Regional Analysis''' in response

    def test_number_of_entries(self):
        url_ = url(controller='dataset', action='view', id='cra')
        response = self.app.get(url_)
        h.assert_equal(response.tmpl_context.num_entries, 36)
