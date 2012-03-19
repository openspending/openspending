from .. import ControllerTestCase, url, helpers as h


class TestViewController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestViewController, self).setup()
        self.user = h.make_account('test')
        h.load_fixture('cra', self.user)
        #h.clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='view',
            action='index', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert 'Library of visualisations' in response.body

    def test_new(self):
        response = self.app.get(url(controller='view',
            action='new', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert 'Select visualisation' in response.body

    def test_embed(self):
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                        params={'widget': 'treemap'})
        assert u"Embedded" in response.body, response.body
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
            expect_errors=True)
        assert "400" in response.status, response.status

    def test_embed_state(self):
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                        params={'widget': 'treemap',
                                'state': '{"foo":"banana"}'})
        assert u"banana" in response.body, response.body
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                        params={'widget': 'treemap',
                                'state': '{"foo:"banana"}'},
            expect_errors=True)
        assert "400" in response.status, response.status
