from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture
from openspending.ui.lib import helpers

from openspending.model import meta as db
from openspending.model.badge import Badge
from pylons import config, url
import json
import os


class TestBadgeController(ControllerTestCase):

    def setup(self):
        """
        Set up the TestBadgeController. Setup creates two users, one regular
        user (test) and one administrator (admin).
        """
        super(TestBadgeController, self).setup()

        # Create test user
        self.user = make_account('test')

        # Create admin user
        self.admin = make_account('admin')
        self.admin.admin = True
        db.session.commit()

        # Load dataset we use for tests
        self.dataset = load_fixture('cra')

    def test_create_badge_form(self):
        """
        Test to see if create badge form is present on badge index page.
        The test should only be available to administrators. For this we
        check whether badge creation url is present on the html sites.
        """

        # Get badge create url
        create_url = url(controller='badge', action='create')

        # Check for non-users (visitors/guests)
        response = self.app.get(url(controller='badge', action='index'))
        assert create_url not in response.body, \
            "URL to create a badge is present in badge index for non-users"

        # Check for normal users
        response = self.app.get(url(controller='badge', action='index'),
                                extra_environ={'REMOTE_USER': 'test'})
        assert create_url not in response.body, \
            "URL to create a badge is present in badge index for normal users"

        response = self.app.get(url(controller='badge', action='index'),
                                extra_environ={'REMOTE_USER': 'admin'})
        assert create_url in response.body, \
            "URL to create a badge is not present in badge index for admins"

    def test_create_badge(self):
        """
        Test badge creation. Only administrators can create badges.
        To create a badge user must provide label, description and image
        """

        # Get all existing badges (should be zero but we never know)
        badge_json = self.app.get(url(controller='badge', action='index',
                                      format='json'))
        badge_index = json.loads(badge_json.body)
        existing_badges = len(badge_index['badges'])

        # The dummy files we'll upload
        files = [("badge-image", "badge.png", "Test badge file")]

        # Create upload directory if it doesn't exist
        object_upload_dir = os.path.join(
            config['pylons.paths']['static_files'],
            config.get('openspending.upload_directory', 'test_uploads'))

        if os.path.isdir(object_upload_dir):
            # Upload dir exists (so we won't change a thing)
            upload_dir_created = False
        else:
            # Doesn't exist (so we'll remove it afterwards
            os.mkdir(object_upload_dir, 0o744)
            upload_dir_created = True

        # Create a new badge (should return unauthorized)
        response = self.app.post(
            url(controller='badge', action='create'),
            params={'badge-label': 'testbadge',
                    'badge-description': 'testdescription'},
            upload_files=files,
            expect_errors=True)

        # Check if it returned Forbidden (which is http status code 403)
        # This should actually return 401 Unauthorized but that's an
        # authentication implementation failure (which should be fixed)
        assert '403' in response.status, \
            "Non-user should get an error when trying to create a badge"

        # Check to see that badge list didn't change
        badge_json = self.app.get(url(controller='badge', action='index',
                                      format='json'))
        assert badge_index == json.loads(badge_json.body), \
            "A non-user was able to change the existing badges"

        # Create a new badge (should return forbidden)
        response = self.app.post(
            url(controller='badge', action='create'),
            params={'badge-label': 'testbadge',
                    'badge-description': 'testdescription'},
            upload_files=files,
            extra_environ={'REMOTE_USER': 'test'},
            expect_errors=True)

        # Check if it returned Forbidden (which is http status code 403)
        assert '403' in response.status, \
            "Non-admin user should get an error when trying to create a badge"

        # Check to see that badge list didn't change
        badge_json = self.app.get(url(controller='badge', action='index',
                                      format='json'))
        assert badge_index == json.loads(badge_json.body), \
            "A non-admin user was able to change the existing badges"

        response = self.app.post(
            url(controller='badge', action='create'),
            params={'badge-label': 'testbadge',
                    'badge-description': 'testdescription'},
            upload_files=files,
            extra_environ={'REMOTE_USER': 'admin'})

        # Check to see there is now badge more in the list than to begin with
        badge_json = self.app.get(url(controller='badge', action='index',
                                      format='json'))
        badge_index = json.loads(badge_json.body)
        assert len(badge_index['badges']) == existing_badges + 1, \
            "One badge should have been added but it wasn't"

        # Check image exists
        # Get image filename from url
        image = badge_index['badges'][0]['image'].split('/')[-1]
        # Get the uploaded file on the system
        upload_dir = helpers.get_object_upload_dir(Badge)
        uploaded_file = os.path.join(upload_dir, image)
        # Check if file exists
        assert os.path.exists(uploaded_file), \
            "Uploaded badge image isn't present on the file system"
        # Remove the file or we'll have a lot of random files after test runs
        os.remove(uploaded_file)

        # If we have created the upload directory we should remove upload_dir
        if upload_dir_created:
            os.rmdir(upload_dir)
            os.rmdir(object_upload_dir)

        # Check to be certain both label and description are present
        assert badge_index['badges'][0]['label'] == 'testbadge', \
            "Uploaded badge label isn't correct"
        assert badge_index['badges'][0]['description'] == 'testdescription', \
            "Uploaded badge description isn't correct"

        # No datasets should be present for the badge just after creation
        assert len(badge_index['badges'][0]['datasets']) == 0, \
            "Newly created badge shouldn't have been awarded to datasets"

    def test_give_badge_form(self):
        """
        Test if badge giving form is only present for admin users on about
        page. Only administrators should see a form to award a badge on the
        about page for a given dataset.
        """

        # Get badge create url
        badge_give_url = url(controller='badge', action='give',
                             dataset=self.dataset.name)

        # Check for non-users (visitors/guests)
        response = self.app.get(url(controller='dataset', action='about',
                                    dataset=self.dataset.name))
        assert badge_give_url not in response.body, \
            "URL to give dataset a badge is in about page for non-users"

        # Check for normal users
        response = self.app.get(url(controller='dataset', action='about',
                                    dataset=self.dataset.name),
                                extra_environ={'REMOTE_USER': 'test'})
        assert badge_give_url not in response.body, \
            "URL to give dataset a badge is in about page for normal users"

        response = self.app.get(url(controller='dataset', action='about',
                                    dataset=self.dataset.name),
                                extra_environ={'REMOTE_USER': 'admin'})
        assert badge_give_url in response.body, \
            "URL to give dataset a badge isn't in about page for admins"

    def test_give_badge(self):
        """
        Test giving dataset a badge. Only administrators should be able to
        give datasets a badge.
        """

        badge = Badge('give-me', 'testimage', 'give me', self.admin)
        db.session.add(badge)
        db.session.commit()

        # Check if non-user can award badges
        response = self.app.post(url(controller='badge', action='give',
                                     dataset='cra'),
                                 params={'badge': badge.id},
                                 expect_errors=True)
        # Check if it returned Forbidden (which is http status code 403)
        # This should actually return 401 Unauthorized but that's an
        # authentication implementation failure (which should be fixed)
        assert '403' in response.status, \
            "Non-user should get an error when trying to give a badge"

        # Check to see that badge hasn't been awarded to any datasets
        badge_json = self.app.get(url(controller='badge', action='information',
                                      id=badge.id, format='json'))
        badge_info = json.loads(badge_json.body)
        assert len(badge_info['badge']['datasets']) == 0, \
            "A non-user was able to award a badge"

        # Check if normal user can award badges
        response = self.app.post(url(controller='badge', action='give',
                                     dataset='cra'),
                                 params={'badge': badge.id},
                                 extra_environ={'REMOTE_USER': 'test'},
                                 expect_errors=True)
        # Check if it returned Forbidden (which is http status code 403)
        assert '403' in response.status, \
            "A normal user should get an error when trying to give a badge"

        # Check to see that badge hasn't been awarded to any datasets
        badge_json = self.app.get(url(controller='badge', action='information',
                                      id=badge.id, format='json'))
        badge_info = json.loads(badge_json.body)
        assert len(badge_info['badge']['datasets']) == 0, \
            "A normal user was able to award a badge"

        # Finally we check if admin user can award badges
        response = self.app.post(url(controller='badge', action='give',
                                     dataset='cra'),
                                 params={'badge': 'not an id'},
                                 extra_environ={'REMOTE_USER': 'admin'},
                                 expect_errors=True)

        # Check to see that badge hasn't been awarded to the dataset
        badge_json = self.app.get(url(controller='badge', action='information',
                                      id=badge.id, format='json'))
        badge_info = json.loads(badge_json.body)
        # Check if admin was able to give the badge to a dataset
        assert len(badge_info['badge']['datasets']) == 0, \
            "Admin user was able to award a badge"

        # Finally we check if admin user can award badges
        response = self.app.post(url(controller='badge', action='give',
                                     dataset='cra'),
                                 params={'badge': badge.id},
                                 extra_environ={'REMOTE_USER': 'admin'})

        # Check to see that badge has been awarded to the dataset
        badge_json = self.app.get(url(controller='badge', action='information',
                                      id=badge.id, format='json'))
        badge_info = json.loads(badge_json.body)
        # Check if admin was able to give the badge to a dataset
        assert len(badge_info['badge']['datasets']) == 1, \
            "Admin user wasn't able to award a badge"
        # Check if admin gave it to the write dataset
        assert self.dataset.name in badge_info['badge']['datasets'], \
            "Admin user gave the badge to the incorrect dataset"
