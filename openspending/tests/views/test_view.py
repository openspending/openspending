import json
from flask import url_for

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture

from openspending.model.dataset import Dataset
from openspending.model.view import View


class TestViewController(ControllerTestCase):

    def setUp(self):
        super(TestViewController, self).setUp()
        self.user = make_account('test')
        load_fixture('cra', self.user)

    def test_index(self):
        response = self.client.get(url_for('view.index', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'Library of visualisations' in response.body

    def test_delete(self):
        # TODO: Create the view using a fixture
        self.client.post(url_for('view.create', dataset='cra'),
                         data={'widget': 'treemap',
                               'label': 'I am a banana!',
                               'state': '{"foo":"banana"}'},
                         query_string={'api_key': self.user.api_key})

        r = self.client.delete(url_for('view.delete', dataset='cra',
                                       name='i-am-a-banana'),
                               query_string={'api_key': self.user.api_key})
        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view is None
        assert '302' in r.status

    def test_delete_by_unauthorized_user(self):
        # TODO: Create the view using a fixture
        self.client.post(url_for('view.create', dataset='cra'),
                         data={'widget': 'treemap',
                               'label': 'I am a banana!',
                               'state': '{"foo":"banana"}'},
                         query_string={'api_key': self.user.api_key})
        response = self.client.delete(
            url_for('view.delete', dataset='cra', name='i-am-a-banana'),
            query_string={'api_key': 'xxx'})

        dataset = Dataset.by_name('cra')
        view = View.by_name(dataset, 'i-am-a-banana')
        assert view is not None
        assert '403' in response.status

    def test_new(self):
        response = self.client.get(url_for('view.new', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'widgets.js' in response.body

    def test_create_noauth(self):
        response = self.client.post(url_for('view.create', dataset='cra'),
                                    data={'widget': 'treemap',
                                          'label': 'I am a banana!',
                                          'state': '{"foo":"banana"}'})
        assert '403' in response.status, response.status

    def test_create(self):
        response = self.client.post(url_for('view.create', dataset='cra'),
                                    data={'widget': 'treemap',
                                          'label': 'I am a banana!',
                                          'state': '{"foo":"banana"}'},
                                    query_string={'api_key': self.user.api_key})
        assert '302' in response.status, response.status
        assert '/cra/views/i-am-a-banana' \
            in response.headers.get('location'), response.headers

        response = self.client.get(url_for('view.view', dataset='cra',
                                           name='i-am-a-banana',
                                           format='json'))
        data = json.loads(response.body)
        assert data['widget'] == 'treemap', data

        response = self.client.get(url_for('view.view', dataset='cra',
                                           name='i-am-a-banana'))
        assert 'title>I am a banana!' in response.body, response

    def test_update(self):
        """
        Test the update function of a view.
        """
        # Create the view (we do it via a controller but it would be
        # better to create it manually (or via a fixture)
        self.client.post(url_for('view.create', dataset='cra'),
                         data={'widget': 'treemap',
                               'label': 'I am a banana!',
                               'state': '{"foo":"banana"}'},
                         query_string={'api_key': self.user.api_key})

        # Check whether a non-user can update the view
        response = self.client.post(url_for('view.update', dataset='cra',
                                            name='i-am-a-banana'),
                                    data={'label': 'I am an apple',
                                          'state': '{"foo":"apple"}',
                                          'description': 'An apple!'})
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
        response = self.client.post(url_for('view.update', dataset='cra',
                                            name='i-am-a-banana'),
                                    data={'label': 'I am an apple',
                                          'state': '{"foo":"apple"}',
                                          'description': 'An apple!'},
                                    query_string={'api_key': 'foo'})
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
        response = self.client.post(url_for('view.update', dataset='cra',
                                            name='i-am-a-banana'),
                                    data={'label': 'I am an apple',
                                          'name': 'can-i-be-an-apple',
                                          'state': '{"foo":"apple"}',
                                          'description': 'An apple!'},
                                    query_string={'api_key': self.user.api_key})

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
        response = self.client.get(url_for('view.embed', dataset='cra'),
                                   data={'widget': 'treemap'})
        assert u"Embedded" in response.body, response.body
        response = self.client.get(url_for('view.embed', dataset='cra'))
        assert "400" in response.status, response.status

    def test_embed_state(self):
        response = self.client.get(url_for('view.embed', dataset='cra'),
                                   data={'widget': 'treemap',
                                         'state': '{"foo":"banana"}'})
        assert u"banana" in response.body, response.body
        response = self.client.get(url_for('view.embed', dataset='cra'),
                                   data={'widget': 'treemap',
                                         'state': '{"foo:"banana"}'})
        assert "400" in response.status, response.status
