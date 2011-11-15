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


