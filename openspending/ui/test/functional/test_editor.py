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
            action='overview', dataset='cra'),
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
