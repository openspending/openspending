from flask import url_for

from openspending.tests.helpers import make_account
from openspending.tests.base import ControllerTestCase
from openspending.tests.importer.test_csv import csvimport_fixture
from openspending.model.account import Account
from openspending.importer import CSVImporter
from openspending.lib.filters import readable_url


class TestRunController(ControllerTestCase):

    def setUp(self):
        super(TestRunController, self).setUp()
        self.source = csvimport_fixture('import_errors')
        self.source.dataset.managers.append(Account.by_name('test'))
        self.importer = CSVImporter(self.source)
        self.importer.run()
        self.account = make_account()

    def test_view_run(self):
        response = self.client.get(url_for('run.view',
                                           dataset=self.source.dataset.name,
                                           source=self.source.id,
                                           id=self.importer._run.id),
                                   query_string={'api_key': self.account.api_key})
        assert readable_url(self.source.url).encode('utf-8') in response.data

    def test_view_run_does_not_exist(self):
        response = self.client.get(url_for('run.view',
                                           dataset=self.source.dataset.name,
                                           source=self.source.id,
                                           id=47347893),
                                   query_string={'api_key': self.account.api_key})
        assert '404' in response.status, response.status
