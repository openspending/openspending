import csv
import json
from StringIO import StringIO

from .. import ControllerTestCase, url, helpers as h
from openspending.model import Dataset, Source, meta as db

class TestSourceController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestSourceController, self).setup()
        self.user = h.make_account('test')
        self.dataset = h.load_fixture('cra', self.user)
        #h.clean_and_reindex_solr()

    def test_view_source(self):
        url_ = 'http://banana.com/split.csv'
        source = Source(self.dataset, self.user, url_)
        db.session.add(source)
        db.session.commit()
        response = self.app.get(url(controller='source', 
            action='view', dataset='cra', id=source.id),
            extra_environ={'REMOTE_USER': 'test'})
        assert response.headers['Location']==url_, response.headers
    
    def test_view_source_does_not_exist(self):
        response = self.app.get(url(controller='source', 
            action='view', dataset='cra', id=47347893),
            extra_environ={'REMOTE_USER': 'test'},
            expect_errors=True)
        assert '404' in response.status, response.status
    
    def test_new_source(self):
        response = self.app.get(url(controller='source', 
            action='new', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert 'Create a data source' in response.body

    def test_create_source(self):
        url_ = 'http://banana.com/split.csv'
        response = self.app.post(url(controller='source', 
            action='create', dataset='cra'),
            params={'url': url_},
            extra_environ={'REMOTE_USER': 'test'})

        response = self.app.get(url(controller='editor', 
            action='index', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert url_ in response.body, response.body

    def test_create_source_invalid_url(self):
        url_ = 'banana'
        response = self.app.post(url(controller='source', 
            action='create', dataset='cra'),
            params={'url': url_},
            extra_environ={'REMOTE_USER': 'test'})
        assert 'HTTP/HTTPS' in response.body
        
        response = self.app.get(url(controller='editor', 
            action='index', dataset='cra'),
            extra_environ={'REMOTE_USER': 'test'})
        assert url_ not in response.body, response.body

