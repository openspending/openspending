import csv
import json
import datetime
from StringIO import StringIO

from openspending.model import Dataset, meta as db
from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import (make_account, load_fixture,
                                        clean_and_reindex_solr)

from pylons import url


class TestDatasetController(ControllerTestCase):

    def setup(self):

        super(TestDatasetController, self).setup()
        self.dataset = load_fixture('cra')
        self.user = make_account('test')
        clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='dataset', action='index'))
        assert 'The database contains the following datasets' in response
        assert 'cra' in response

    def test_index_json(self):
        response = self.app.get(
            url(controller='dataset', action='index', format='json'))
        obj = json.loads(response.body)
        assert len(obj['datasets']) == 1
        assert obj['datasets'][0]['name'] == 'cra'
        assert obj['datasets'][0]['label'] == 'Country Regional Analysis v2009'

    def test_index_hide_private(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.app.get(
            url(controller='dataset', action='index', format='json'))
        obj = json.loads(response.body)
        assert len(obj['datasets']) == 0

    def test_index_csv(self):
        response = self.app.get(
            url(controller='dataset', action='index', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        assert len(obj) == 1
        assert obj[0]['name'] == 'cra'
        assert obj[0]['label'] == 'Country Regional Analysis v2009'

    def test_view(self):
        """
        Test view page for a dataset
        """

        # Get the view page for the dataset
        response = self.app.get(
            url(controller='dataset', action='view', dataset='cra'))
        # The dataset label should be present in the response
        assert 'Country Regional Analysis v2009' in response, \
            "'Country Regional Analysis v2009' not in response!"

        # Assertions about time range
        assert 'Time range' in response.body, \
            'Time range is not present on view page for dataset'
        # Start date comes from looking at the test fixture for cra
        assert '2003-01-01' in response.body, \
            'Starting date of time range not on view page for dataset'
        # End date comes from looking at the test fixture for cra
        assert '2010-01-01' in response.body, \
            'End date of time range not on view page for dataset'

    def test_view_private(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='view',
                                    dataset='cra'), status=403)
        assert 'Country Regional Analysis v2009' not in response, \
            "'Country Regional Analysis v2009' in response!"
        assert 'openspending_browser' not in response, \
            "'openspending_browser' in response!"

    def test_about_has_format_links(self):
        url_ = url(controller='dataset', action='about', dataset='cra')
        response = self.app.get(url_)

        url_ = url(controller='dataset', action='model', dataset='cra',
                   format='json')

        assert url_ in response, \
            "Link to view page (JSON format) not in response!"

    def test_about_has_profile_links(self):
        self.dataset.managers.append(self.user)
        db.session.add(self.dataset)
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='about',
                                    dataset='cra'))
        profile_url = url(controller='account', action='profile',
                          name=self.user.name)
        profile_link = '<li><a href="{url}">{fullname}</a></li>'.format(
            url=profile_url, fullname=self.user.fullname)
        assert profile_link in response.body

    def test_about_has_timestamps(self):
        """
        Test whether about page includes timestamps when dataset was created
        and when it was last updated
        """

        # Get the about page
        response = self.app.get(url(controller='dataset', action='about',
                                    dataset='cra'))

        # Check assertions for timestamps
        assert 'Timestamps' in response.body, \
            'Timestamp header is not on about page'
        assert 'created on' in response.body, \
            'No line for "created on" on about page'
        assert 'last modified on' in response.body, \
            'No line for "last modified on" on about page'
        assert datetime.datetime.now().strftime('%Y-%m-%d') in response.body, \
            'Created (and update) timestamp is not on about page'

    def test_view_json(self):
        response = self.app.get(url(controller='dataset', action='view',
                                    dataset='cra', format='json'))
        obj = json.loads(response.body)
        assert obj['name'] == 'cra'
        assert obj['label'] == 'Country Regional Analysis v2009'

    def test_model_json(self):
        response = self.app.get(url(controller='dataset', action='model',
                                    dataset='cra', format='json'))
        obj = json.loads(response.body)
        assert 'dataset' in obj.keys(), obj
        assert obj['dataset']['name'] == 'cra'
        assert obj['dataset']['label'] == 'Country Regional Analysis v2009'

    def test_entries_json_export(self):
        response = self.app.get(url(controller='entry',
                                    action='index',
                                    dataset='cra',
                                    format='json'))
        assert '/api/2/search' in response.headers['Location'], \
            response.headers
        assert 'format=json' in response.headers['Location'], response.headers

    def test_entries_csv_export(self):
        response = self.app.get(url(controller='entry',
                                    action='index',
                                    dataset='cra',
                                    format='csv'))
        assert '/api/2/search' in response.headers['Location'], \
            response.headers
        assert 'format=csv' in response.headers['Location'], response.headers
        response = response.follow()
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        assert len(obj) == 36

    def test_new_form(self):
        response = self.app.get(url(controller='dataset', action='new'),
                                params={'limit': '20'},
                                extra_environ={'REMOTE_USER': 'test'})
        assert "Import a dataset" in response.body

    def test_create_dataset(self):
        response = self.app.post(url(controller='dataset', action='create'),
                                 extra_environ={'REMOTE_USER': 'test'})
        assert "Import a dataset" in response.body
        assert "Required" in response.body

        params = {'name': 'testds', 'label': 'Test Dataset',
                  'category': 'budget', 'description': 'I\'m a banana!',
                  'currency': 'EUR'}

        response = self.app.post(url(controller='dataset', action='create'),
                                 params=params,
                                 extra_environ={'REMOTE_USER': 'test'})
        assert "302" in response.status

        ds = Dataset.by_name('testds')
        assert ds.label == params['label'], ds

    def test_feeds(self):
        # Anonymous user with one public dataset
        response = self.app.get(url(controller='dataset', action='feed_rss'),
                                expect_errors=True)
        assert 'application/xml' in response.content_type
        assert '<title>Recently Created Datasets</title>' in response
        assert '<item><title>Country Regional Analysis v2009' in response
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.add(cra)
        db.session.commit()

        # Anonymous user with one private dataset
        response = self.app.get(url(controller='dataset', action='feed_rss'),
                                expect_errors=True)
        assert 'application/xml' in response.content_type
        assert '<title>Recently Created Datasets</title>' in response
        assert '<item><title>Country Regional Analysis v2009' not in response

        # Logged in user with one public dataset
        cra.private = False
        db.session.add(cra)
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='feed_rss'),
                                expect_errors=True,
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'application/xml' in response.content_type
        assert '<title>Recently Created Datasets</title>' in response
        assert '<item><title>Country Regional Analysis v2009' in response

        # Logged in user with one private dataset
        cra.private = True
        db.session.add(cra)
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='feed_rss'),
                                expect_errors=True,
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'application/xml' in response.content_type
        assert '<title>Recently Created Datasets</title>' in response
        assert '<item><title>Country Regional Analysis v2009' not in response

        # Logged in admin user with one private dataset
        admin_user = make_account('admin')
        admin_user.admin = True
        db.session.add(admin_user)
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='feed_rss'),
                                extra_environ={'REMOTE_USER': 'admin'})
        assert '<title>Recently Created Datasets</title>' in response
        assert '<item><title>Country Regional Analysis v2009' in response
        assert 'application/xml' in response.content_type

        response = self.app.get(url(controller='dataset', action='index'))
        assert ('<link rel="alternate" type="application/rss+xml" title="'
                'Latest Datasets on OpenSpending" href="/datasets.rss"' in
                response)
