import json

from .. import ControllerTestCase, url, helpers as h
from openspending.model import Dataset, Source, meta as db


class TestEditorController(ControllerTestCase):

    def setup(self):

        super(TestEditorController, self).setup()
        self.user = h.make_account('test')
        h.load_fixture('cra', self.user)
        # h.clean_and_reindex_solr()

    def test_overview(self):
        response = self.app.get(url(controller='editor',
                                    action='index', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'Manage the dataset' in response.body

    def test_core_edit_mask(self):
        response = self.app.get(url(controller='editor',
                                    action='core_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'EUR' in response.body
        assert 'Update' in response.body

    def test_core_update(self):
        self.app.post(url(controller='editor',
                          action='core_update', dataset='cra'),
                      params={'name': 'cra', 'label': 'Common Rough Act',
                              'description': 'I\'m a banana', 'currency': 'EUR',
                              'languages': 'en', 'territories': 'gb',
                              'category': 'budget', 'default_time': 2009},
                      extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert cra.label == 'Common Rough Act', cra.label
        assert cra.currency == 'EUR', cra.currency

    def test_core_update_invalid_category(self):
        response = self.app.post(url(controller='editor',
                                     action='core_update', dataset='cra'),
                                 params={'name': 'cra', 'label': 'Common Rough Act',
                                         'description': 'I\'m a banana', 'currency': 'EUR',
                                         'languages': 'en', 'territories': 'gb',
                                         'category': 'foo', 'default_time': 2009},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert 'valid category' in response.body
        cra = Dataset.by_name('cra')
        assert cra.label != 'Common Rough Act', cra.label

    def test_core_update_invalid_label(self):
        response = self.app.post(url(controller='editor',
                                     action='core_update', dataset='cra'),
                                 params={'name': 'cra', 'label': '',
                                         'description': 'I\'m a banana', 'currency': 'GBP'},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert 'Required' in response.body
        cra = Dataset.by_name('cra')
        assert cra.label != '', cra.label

    def test_core_update_invalid_language(self):
        response = self.app.post(url(controller='editor',
                                     action='core_update', dataset='cra'),
                                 params={'name': 'cra', 'label': 'CRA', 'languages': 'esperanto',
                                         'description': 'I\'m a banana', 'currency': 'GBP',
                                         'default_time': 2009},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert not 'updated' in response.body
        cra = Dataset.by_name('cra')
        assert not 'esperanto' in cra.languages

    def test_core_update_invalid_territory(self):
        response = self.app.post(url(controller='editor',
                                     action='core_update', dataset='cra'),
                                 params={'name': 'cra', 'label': 'CRA', 'territories': 'su',
                                         'description': 'I\'m a banana', 'currency': 'GBP',
                                         'default_time': 2009},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert not 'updated' in response.body
        cra = Dataset.by_name('cra')
        assert not 'su' in cra.territories

    def test_core_update_invalid_currency(self):
        response = self.app.post(url(controller='editor',
                                     action='core_update', dataset='cra'),
                                 params={'name': 'cra', 'label': 'Common Rough Act',
                                         'description': 'I\'m a banana', 'currency': 'glass pearls',
                                         'default_time': 2009},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert 'not a valid currency' in response.body
        cra = Dataset.by_name('cra')
        assert cra.currency == 'GBP', cra.label

    def test_dimensions_edit_mask(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.init()
        cra.generate()
        src = Source(cra, self.user, 'file:///dev/null')
        src.analysis = {'columns': ['amount', 'etc']}
        db.session.add(src)
        db.session.commit()
        response = self.app.get(url(controller='editor',
                                    action='dimensions_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert '"amount"' in response.body
        assert 'Update' in response.body

    def test_dimensions_edit_mask_with_data(self):
        cra = Dataset.by_name('cra')
        src = Source(cra, self.user, 'file:///dev/null')
        src.analysis = {'columns': ['amount', 'etc']}
        db.session.add(src)
        db.session.commit()
        response = self.app.get(url(controller='editor',
                                    action='dimensions_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'cannot edit dimensions' in response.body
        assert '"amount"' not in response.body
        assert 'Update' not in response.body

    def test_dimensions_update_invalid_json(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.init()
        cra.generate()
        response = self.app.post(url(controller='editor',
                                     action='dimensions_update', dataset='cra'),
                                 params={'mapping': 'banana'},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '400' in response.status, response.status

    def test_views_edit_mask(self):
        response = self.app.get(url(controller='editor',
                                    action='views_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert '"default"' in response.body
        assert 'Update' in response.body

    def test_views_update(self):
        cra = Dataset.by_name('cra')
        views = cra.data['views']
        views[0]['label'] = 'Banana'
        response = self.app.post(url(controller='editor',
                                     action='views_update', dataset='cra'),
                                 params={'views': json.dumps(views)},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert 'Banana' in repr(cra.data['views'])

    def test_views_update_invalid_json(self):
        response = self.app.post(url(controller='editor',
                                     action='views_update', dataset='cra'),
                                 params={'views': 'banana'},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '400' in response.status, response.status

    def test_team_edit_mask(self):
        response = self.app.get(url(controller='editor',
                                    action='team_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'Add someone' in response.body
        assert 'Save' in response.body

    def test_team_update(self):
        response = self.app.post(url(controller='editor',
                                     action='team_update', dataset='cra'),
                                 params={},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert len(cra.managers.all()) == 1, cra.managers

    def test_templates_edit_mask(self):
        response = self.app.get(url(controller='editor',
                                    action='templates_edit', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'Update' in response.body

    def test_templates_update(self):
        response = self.app.post(url(controller='editor',
                                     action='templates_update', dataset='cra'),
                                 params={'serp_title': 'BANANA'},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert cra.serp_title == 'BANANA', cra.serp_title

    def test_drop(self):
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)
        # double-check authz
        response = self.app.post(url(controller='editor',
                                     action='drop', dataset='cra'),
                                 expect_errors=True)
        assert '403' in response.status
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)

        response = self.app.post(url(controller='editor',
                                     action='drop', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert len(cra) == 0, len(cra)

    def test_delete(self):
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)
        # double-check authz
        response = self.app.post(url(controller='editor',
                                     action='delete', dataset='cra'),
                                 expect_errors=True)
        assert '403' in response.status
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)

        response = self.app.post(url(controller='editor',
                                     action='delete', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert cra is None, cra

    def test_publish(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.app.post(url(controller='editor',
                                     action='publish', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert cra.private is False, cra.private
        response = self.app.post(url(controller='editor',
                                     action='publish', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '400' in response.status, response.status

    def test_retract(self):
        cra = Dataset.by_name('cra')
        assert cra.private is False, cra.private
        response = self.app.post(url(controller='editor',
                                     action='retract', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert cra.private is True, cra.private
        response = self.app.post(url(controller='editor',
                                     action='retract', dataset='cra'),
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        assert '400' in response.status, response.status
