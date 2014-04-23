from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture
from openspending.tests.importer.test_csv import csvimport_fixture

from openspending.model import Source, Account, meta as db
from openspending.importer import CSVImporter

from pylons import url


class TestSourceController(ControllerTestCase):

    def setup(self):

        super(TestSourceController, self).setup()
        self.user = make_account('test')
        self.dataset = load_fixture('cra', self.user)

    def test_view_source(self):
        url_ = 'http://banana.com/split.csv'
        source = Source(self.dataset, self.user, url_)
        db.session.add(source)
        db.session.commit()
        response = self.app.get(url(controller='source',
                                    action='view', dataset='cra',
                                    id=source.id),
                                extra_environ={'REMOTE_USER': 'test'})
        assert response.headers['Location'] == url_, response.headers

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

    def test_delete_source(self):
        """
        Test source removal with a source that includes errors
        """

        # Add and import source with errors (we want to remove it)
        # The source is added to a dataset called 'test-csv' (but
        # we'll just use source.dataset.name in case it changes)
        source = csvimport_fixture('import_errors')
        source.dataset.managers.append(Account.by_name('test'))
        importer = CSVImporter(source)
        importer.run()

        # Make sure the source is imported
        assert db.session.query(Source).filter_by(id=source.id).count() == 1, \
            "Import of csv failed. Source not found"

        # Delete the source
        self.app.post(url(controller='source',
                          action='delete',
                          dataset=source.dataset.name,
                          id=source.id),
                      extra_environ={'REMOTE_USER': 'test'})

        # Check if source has been deleted
        assert db.session.query(Source).filter_by(id=source.id).count() == 0, \
            "Deleting source unsuccessful. Source still exists."

    def test_delete_successfully_loaded_source(self):
        """
        Test source removal with a source that has been successfully loaded.
        Removing a source that has been successfully loaded should not be
        possible.
        """

        # Add and import source without errors.
        # The source is added to a dataset called 'test-csv' (but
        # we'll just use source.dataset.name in case it changes)
        source = csvimport_fixture('successful_import')
        source.dataset.managers.append(Account.by_name('test'))
        importer = CSVImporter(source)
        importer.run()

        # Make sure the source is imported
        assert db.session.query(Source).filter_by(id=source.id).count() == 1, \
            "Import of csv failed. Source not found"

        # Delete the source
        self.app.post(url(controller='source',
                          action='delete',
                          dataset=source.dataset.name,
                          id=source.id),
                      extra_environ={'REMOTE_USER': 'test'})

        # Check if source has been deleted
        assert db.session.query(Source).filter_by(id=source.id).count() == 1, \
            "Deleting source succeeded. The source is gone."
