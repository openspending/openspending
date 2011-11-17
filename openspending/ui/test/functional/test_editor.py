import csv
import json
from StringIO import StringIO

from .. import ControllerTestCase, url, helpers as h
from openspending.model import Dataset, meta as db

class TestEditorController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestEditorController, self).setup()
        user = h.make_account('test')
        h.load_fixture('cra', user)
        #h.clean_and_reindex_solr()

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
        response = self.app.post(url(controller='editor', 
            action='core_update', dataset='cra'),
            params={'name': 'cra', 'label': 'Common Rough Act',
                    'description': 'I\'m a banana', 'currency': 'EUR'},
            extra_environ={'REMOTE_USER': 'test'})
        cra = Dataset.by_name('cra')
        assert cra.label=='Common Rough Act', cra.label
        assert cra.dataset['label']=='Common Rough Act', cra.dataset
        assert cra.currency=='EUR', cra.currency
    
    def test_core_update_invalid_label(self):
        response = self.app.post(url(controller='editor', 
            action='core_update', dataset='cra'),
            params={'name': 'cra', 'label': '',
                    'description': 'I\'m a banana', 'currency': 'GBP'},
            extra_environ={'REMOTE_USER': 'test'})
        assert 'Required' in response.body
        cra = Dataset.by_name('cra')
        assert cra.label!='Common Rough Act', cra.label
        assert cra.dataset['label']!='Common Rough Act', cra.dataset
    
    def test_core_update_invalid_currency(self):
        response = self.app.post(url(controller='editor', 
            action='core_update', dataset='cra'),
            params={'name': 'cra', 'label': 'Common Rough Act',
                    'description': 'I\'m a banana', 'currency': 'glass pearls'},
            extra_environ={'REMOTE_USER': 'test'})
        assert 'not a valid currency' in response.body
        cra = Dataset.by_name('cra')
        assert cra.currency=='GBP', cra.label

    def test_dimensions_edit_mask(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.generate()
        response = self.app.get(url(controller='editor', 
            action='dimensions_edit', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert '"amount"' in response.body
        assert 'Update' in response.body
    
    def test_dimensions_edit_mask_with_data(self):
        response = self.app.get(url(controller='editor', 
            action='dimensions_edit', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert 'cannot edit dimensions' in response.body
        assert '"amount"' not in response.body
        assert 'Update' not in response.body

    def test_dimensions_update_invalid_json(self):
        cra = Dataset.by_name('cra')
        cra.drop()
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

