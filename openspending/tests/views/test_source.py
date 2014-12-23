from flask import url_for

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture
from openspending.tests.importer.test_csv import csvimport_fixture

from openspending.core import db
from openspending.model.source import Source
from openspending.model.account import Account
from openspending.importer import CSVImporter


class TestSourceController(ControllerTestCase):

    def setUp(self):

        super(TestSourceController, self).setUp()
        self.user = make_account('test')
        self.dataset = load_fixture('cra', self.user)

    def test_view_source(self):
        url_ = 'http://banana.com/split.csv'
        source = Source(self.dataset, self.user, url_)
        db.session.add(source)
        db.session.commit()
        response = self.client.get(url_for('source.view', dataset='cra', id=source.id),
                                   query_string={'api_key': self.user.api_key})
        assert response.headers['Location'] == url_, response.headers

    def test_view_source_does_not_exist(self):
        response = self.client.get(url_for('source.view', dataset='cra', id=47347893),
                                   query_string={'api_key': self.user.api_key})
        assert '404' in response.status, response.status

    def test_new_source(self):
        response = self.client.get(url_for('source.new', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'Create a data source' in response.data

    def test_create_source(self):
        url_ = 'http://banana.com/split.csv'
        response = self.client.post(url_for('source.create', dataset='cra'),
                                    data={'url': url_},
                                    query_string={'api_key': self.user.api_key})

        response = self.client.get(url_for('editor.index', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert url_ in response.data, response.data

    def test_create_source_invalid_url(self):
        url_ = 'banana'
        response = self.client.post(url_for('source.create', dataset='cra'),
                                    data={'url': url_},
                                    query_string={'api_key': self.user.api_key})
        assert 'HTTP/HTTPS' in response.data

        response = self.client.get(url_for('editor.index', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert url_ not in response.data, response.data

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
        self.client.post(url_for('source.delete', dataset=source.dataset.name,
                                 id=source.id),
                         query_string={'api_key': self.user.api_key})

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
        self.client.post(url_for('source.delete', dataset=source.dataset.name,
                                 id=source.id),
                         query_string={'api_key': self.user.api_key})

        # Check if source has been deleted
        assert db.session.query(Source).filter_by(id=source.id).count() == 1, \
            "Deleting source succeeded. The source is gone."
