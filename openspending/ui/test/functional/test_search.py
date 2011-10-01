from .. import ControllerTestCase, url, helpers as h

class TestSearchController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestSearchController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_index(self):
        url_ = url(controller='search', action='index')
        response = self.app.get(url_, params={'q': 'transport'})
        assert u'Search' in response, response
        assert u'Department for Transport' in response, response
