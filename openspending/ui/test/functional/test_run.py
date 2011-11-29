import csv
import json
from StringIO import StringIO

from .. import ControllerTestCase, url, helpers as h
from openspending.test.unit.importer.test_csv import csvimport_fixture
from openspending.model import Dataset, Source, Account, Run, LogRecord, meta as db
from openspending.importer import CSVImporter

class TestRunController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestRunController, self).setup()
        self.source = csvimport_fixture('import_errors')
        self.source.dataset.managers.append(Account.by_name('test'))
        self.importer = CSVImporter(self.source)
        self.importer.run()

    def test_view_run(self):
        response = self.app.get(url(controller='run', 
            action='view', dataset=self.source.dataset.name,
            source=self.source.id, 
            id=self.importer._run.id),
            extra_environ={'REMOTE_USER': 'test'},
            expect_errors=True)
        assert self.source.name.encode('utf-8') in response.body
    
    def test_view_run_does_not_exist(self):
        response = self.app.get(url(controller='run', 
            action='view', dataset=self.source.dataset.name,
            source=self.source.id, 
            id=47347893),
            extra_environ={'REMOTE_USER': 'test'},
            expect_errors=True)
        assert '404' in response.status, response.status
    
