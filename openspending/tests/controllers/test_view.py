import json

from openspending.tests.base import ControllerTestCase
from openspending.tests import helpers as h
from openspending.model import View, Dataset

from pylons import url


class TestViewController(ControllerTestCase):

    def setup(self):
        super(TestViewController, self).setup()
        self.user = h.make_account('test')
        h.load_fixture('cra', self.user)
        # h.clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='view',
                                    action='index', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'Library of visualisations' in response.body

    def test_delete(self):
        # TODO: Create the view using a fixture
        self.app.post(url(controller='view', action='create',
                          dataset='cra'),
                      params={'widget': 'treemap',
                              'label': 'I am a banana!',
                              'state': '{"foo":"banana"}'},
                      extra_environ={'REMOTE_USER': 'test'})
        response = self.app.delete(url(controller='view',
                                       action='delete', dataset='cra',
                                       name='i-am-a-banana'),
                                   extra_environ={'REMOTE_USER': 'test'})
        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view is None
        assert '302' in response.status

    def test_delete_by_unauthorized_user(self):
        # TODO: Create the view using a fixture
        self.app.post(url(controller='view', action='create',
                          dataset='cra'),
                      params={'widget': 'treemap',
                              'label': 'I am a banana!',
                              'state': '{"foo":"banana"}'},
                      extra_environ={'REMOTE_USER': 'test'})
        response = self.app.delete(
            url(controller='view',
                action='delete', dataset='cra',
                name='i-am-a-banana'),
            expect_errors=True,
            extra_environ={
                'REMOTE_USER': 'unauthorized_user'})

        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view is not None
        assert '403' in response.status

    def test_new(self):
        response = self.app.get(url(controller='view',
                                    action='new', dataset='cra'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert 'widgets.js' in response.body

    def test_create_noauth(self):
        response = self.app.post(url(controller='view', action='create',
                                     dataset='cra'),
                                 params={'widget': 'treemap',
                                         'label': 'I am a banana!',
                                         'state': '{"foo":"banana"}'},
                                 expect_errors=True)
        assert '403' in response.status, response.status

    def test_create(self):
        response = self.app.post(url(controller='view', action='create',
                                     dataset='cra'),
                                 params={'widget': 'treemap',
                                         'label': 'I am a banana!',
                                         'state': '{"foo":"banana"}'},
                                 extra_environ={'REMOTE_USER': 'test'})
        assert '302' in response.status, response.status
        assert '/cra/views/i-am-a-banana' \
            in response.headers.get('location'), response.headers

        response = self.app.get(url(controller='view', action='view',
                                    dataset='cra', name='i-am-a-banana',
                                    format='json'))
        data = json.loads(response.body)
        assert data['widget'] == 'treemap', data

        response = self.app.get(url(controller='view', action='view',
                                    dataset='cra', name='i-am-a-banana'))
        assert 'title>I am a banana!' in response.body, response

    def test_update(self):
        """
        Test the update function of a view.
        """
        # Create the view (we do it via a controller but it would be
        # better to create it manually (or via a fixture)
        self.app.post(url(controller='view', action='create',
                          dataset='cra'),
                      params={'widget': 'treemap',
                              'label': 'I am a banana!',
                              'state': '{"foo":"banana"}'},
                      extra_environ={'REMOTE_USER': 'test'})

        # Check whether a non-user can update the view
        response = self.app.post(url(controller='view', action='update',
                                     dataset='cra', name='i-am-a-banana'),
                                 params={'label': 'I am an apple',
                                         'state': '{"foo":"apple"}',
                                         'description': 'An apple!'},
                                 expect_errors=True)
        # The user should receive a 403 Forbidden (actually should get 401)
        assert '403' in response.status, \
            "A non-user was able to update a view"

        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view.label == 'I am a banana!', \
            "View's label was changed by a non-user"
        assert view.state['foo'] == 'banana', \
            "View's state was changed by a non-user"
        assert view.description is None, \
            "View's description was changed by a non-user"

        # Check whether an unauthorized user can update the view
        response = self.app.post(url(controller='view', action='update',
                                     dataset='cra', name='i-am-a-banana'),
                                 params={'label': 'I am an apple',
                                         'state': '{"foo":"apple"}',
                                         'description': 'An apple!'},
                                 expect_errors=True,
                                 extra_environ={'REMOTE_USER': 'anotheruser'})
        # The user should receive a 403 (Forbidden)
        assert '403' in response.status, \
            "Unauthorized user was able to update a view"

        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view.label == 'I am a banana!', \
            "View's label was changed by an unauthorized user"
        assert view.state['foo'] == 'banana', \
            "View's state was changed by an unauthorized user"
        assert view.description is None, \
            "View's description was changed by an unauthorized user"

        # Check whether a managing user can update the view
        response = self.app.post(url(controller='view', action='update',
                                     dataset='cra', name='i-am-a-banana'),
                                 params={'label': 'I am an apple',
                                         'name': 'can-i-be-an-apple',
                                         'state': '{"foo":"apple"}',
                                         'description': 'An apple!'},
                                 extra_environ={'REMOTE_USER': 'test'})

        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        # Name cannot have been changed because the view might have been
        # embedded elsewhere (cannot be changed by params nor be re-slugified)
        assert view is not None, \
            "View's name was changed by update"
        assert view.label == 'I am an apple', \
            "View's label wasn't changed by the managing user"
        assert view.state['foo'] == 'apple', \
            "View's state wasn't changed by the managing user"
        assert view.description == 'An apple!', \
            "View's description wasn't changed by the managing user"

    def test_embed(self):
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                                params={'widget': 'treemap'})
        assert u"Embedded" in response.body, response.body
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                                expect_errors=True)
        assert "400" in response.status, response.status

    def test_embed_state(self):
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                                params={'widget': 'treemap',
                                        'state': '{"foo":"banana"}'})
        assert u"banana" in response.body, response.body
        response = self.app.get(url(controller='view', action='embed',
                                    dataset='cra'),
                                params={'widget': 'treemap',
                                        'state': '{"foo:"banana"}'},
                                expect_errors=True)
        assert "400" in response.status, response.status
