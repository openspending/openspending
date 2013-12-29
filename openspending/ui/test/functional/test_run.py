from .. import ControllerTestCase, url
from openspending.test.unit.importer.test_csv import csvimport_fixture
from openspending.model import Account
from openspending.importer import CSVImporter
from openspending.ui.lib.helpers import readable_url


class TestRunController(ControllerTestCase):

    def setup(self):

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
        assert readable_url(self.source.url).encode('utf-8') in response.body

    def test_view_run_does_not_exist(self):
        response = self.app.get(url(controller='run',
            action='view', dataset=self.source.dataset.name,
            source=self.source.id,
            id=47347893),
            extra_environ={'REMOTE_USER': 'test'},
            expect_errors=True)
        assert '404' in response.status, response.status
