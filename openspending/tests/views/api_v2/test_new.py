import json
from flask import url_for

from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.model.account import Account

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account
from openspending.tests.helpers import load_fixture


class TestApiNewDataset(ControllerTestCase):

    """
    This checks for authentication with a header api key while also
    testing for loading of data via the api
    """

    def setUp(self):
        super(TestApiNewDataset, self).setUp()
        self.user = make_account('test_new')
        self.user2 = make_account('test_new2')

    def test_new_dataset(self):
        user = Account.by_name('test_new')

        u = url_for('api_v2.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert "200" in response.status
        dataset = Dataset.by_name('openspending-example')
        assert dataset is not None
        assert dataset.private is False

    def test_private_dataset(self):
        user = Account.by_name('test_new')

        u = url_for('api_v2.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'private': 'true'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert "200" in response.status
        dataset = Dataset.by_name('openspending-example')
        assert dataset is not None
        assert dataset.private is True

    def test_new_no_apikey(self):
        u = url_for('api_v2.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params)
        assert "403" in response.status, response.status
        assert Dataset.by_name('openspending-example') is None

    def test_new_wrong_user(self):
        # First we add a Dataset with user 'test_new'
        user = Account.by_name('test_new')
        
        u = url_for('api_v2.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})

        assert "200" in response.status, (response.status, response.data)
        assert Dataset.by_name('openspending-example') is not None

        # After that we try to update the Dataset with user 'test_new2'
        user = Account.by_name('test_new2')
        
        u = url_for('api_v2.create')
        params = {
            'metadata':
            'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':
            'http://mk.ucant.org/info/data/sample-openspending-dataset.csv'
        }
        response = self.client.post(u, data=params,
                                    query_string={'api_key': user.api_key})
        assert '403' in response.status, response.status

    def test_permissions(self):
        """
        Test permissions API which tells users if they are allowed to
        perform CRUD operations on a given dataset
        """

        # Create our users
        admin = make_account('test_admin', admin=True)
        maintainer = make_account('maintainer')
        user = make_account('test_user')
        load_fixture('cra')

        # Set maintainer as maintainer of cra dataset
        dataset = Dataset.by_name('cra')
        dataset.managers.append(maintainer)
        db.session.add(dataset)
        db.session.commit()

        # Make the url reusable
        permission = url_for('api_v2.permissions')

        # First we try to get permissions without dataset parameter
        # This should return a 200 but include an error message and nothing
        # else
        response = self.client.get(permission)
        json_response = json.loads(response.data)
        assert len(json_response.keys()) == 1, \
            'Parameterless call response includes more than one properties'
        assert 'error' in json_response, \
            'Error property not present in parameterless call response'

        # Dataset is public by default

        # Anonymous user
        response = self.client.get(permission, query_string={'dataset': 'cra'})
        anon_response = json.loads(response.data)
        assert not anon_response['create'], \
            'Anonymous user can create existing dataset'
        assert anon_response['read'], \
            'Anonymous user cannot read public dataset'
        assert not anon_response['update'], \
            'Anonymous user can update existing dataset'
        assert not anon_response['delete'], \
            'Anonymous user can delete existing dataset'
        # Normal user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert anon_response == normal_response, \
            'Normal user has wrong permissions for a public dataset'
        # Maintainer
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': maintainer.api_key})
        main_response = json.loads(response.data)
        assert not main_response['create'], \
            'Maintainer can create a dataset with an existing (public) name'
        assert main_response['read'], \
            'Maintainer is not able to read public dataset'
        assert main_response['update'], \
            'Maintainer is not able to update public dataset'
        assert main_response['delete'], \
            'Maintainer is not able to delete public dataset'
        # Administrator
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': admin.api_key})
        admin_response = json.loads(response.data)
        # Permissions for admins should be the same as for maintainer
        assert main_response == admin_response, \
            'Admin and maintainer permissions differ on public datasets'

        # Set cra dataset as private so only maintainer and admin should be
        # able to 'read' (and 'update' and 'delete'). All others should get
        # False on everything
        dataset = Dataset.by_name('cra')
        dataset.private = True
        db.session.add(dataset)
        db.session.commit()

        # Anonymous user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra'})
        anon_response = json.loads(response.data)
        assert True not in anon_response.values(), \
            'Anonymous user has access to a private dataset'
        # Normal user
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert anon_response == normal_response, \
            'Normal user has access to a private dataset'
        # Maintainer
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': maintainer.api_key})
        main_response = json.loads(response.data)
        assert not main_response['create'], \
            'Maintainer can create a dataset with an existing (private) name'
        assert main_response['read'], \
            'Maintainer is not able to read private dataset'
        assert main_response['update'], \
            'Maintainer is not able to update private dataset'
        assert main_response['delete'], \
            'Maintainer is not able to delete private dataset'
        # Administrator
        response = self.client.get(permission,
                                   query_string={'dataset': 'cra',
                                                 'api_key': admin.api_key})
        admin_response = json.loads(response.data)
        # Permissions for admins should be the same as for maintainer
        assert main_response == admin_response, \
            'Admin does not have the same permissions as maintainer'

        # Now we try accessing a nonexistent dataset
        # Everyone except anonymous user should have the same permissions
        # We don't need to check with maintainer or admin now since this
        # applies to all logged in users
        response = self.client.get(permission,
                                   query_string={'dataset': 'nonexistent'})
        anon_response = json.loads(response.data)
        assert True not in anon_response.values(), \
            'Anonymous users has permissions on a nonexistent datasets'
        # Any logged in user (we use normal user)
        response = self.client.get(permission,
                                   query_string={'dataset': 'nonexistent',
                                                 'api_key': user.api_key})
        normal_response = json.loads(response.data)
        assert normal_response['create'], \
            'User cannot create a nonexistent dataset'
        assert not normal_response['read'], \
            'User can read a nonexistent dataset'
        assert not normal_response['update'], \
            'User can update a nonexistent dataset'
        assert not normal_response['delete'], \
            'User can delete a nonexistent dataset'
