from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture
from nose.tools import raises
from mock import patch

from openspending.model import meta as db
from openspending.model.account import Account
from openspending.lib.mailer import MailerException
from pylons import config, url

import json
import urllib2


class TestAccountController(ControllerTestCase):

    def test_login(self):
        self.app.get(url(controller='account', action='login'))

    def test_register(self):
        self.app.get(url(controller='account', action='register'))

    def test_account_create_gives_api_key(self):
        account = make_account()
        assert len(account.api_key) == 36

    @patch('openspending.auth.account.update')
    @patch('openspending.model.account.Account.by_name')
    def test_settings(self, model_mock, update_mock):
        account = Account()
        account.name = 'mockaccount'
        db.session.add(account)
        db.session.commit()
        model_mock.return_value = account
        update_mock.return_value = True
        self.app.get(url(controller='account', action='settings'),
                     extra_environ={'REMOTE_USER': 'mockaccount'})

    def test_after_login(self):
        self.app.get(url(controller='account', action='after_login'))

    def test_after_logout(self):
        self.app.get(url(controller='account', action='after_logout'))

    def test_trigger_reset_get(self):
        response = self.app.get(
            url(controller='account', action='trigger_reset'))
        assert 'email address you used to register your account'\
            in response.body, response.body

    def test_trigger_reset_post_fail(self):
        response = self.app.post(url(controller='account',
                                     action='trigger_reset'),
                                 params={'emailx': "foo@bar"})
        assert 'Please enter an email address' in response.body, response.body
        response = self.app.post(url(controller='account',
                                     action='trigger_reset'),
                                 params={'email': "foo@bar"})
        assert 'No user is registered' in response.body, response.body

    @raises(MailerException)
    def test_trigger_reset_post_ok(self):
        try:
            original_smtp_server = config.get('smtp_server')
            config['smtp_server'] = 'non-existent-smtp-server'
            make_account()
            self.app.post(url(controller='account',
                              action='trigger_reset'),
                          params={'email': "test@example.com"})
        finally:
            config['smtp_server'] = original_smtp_server

    def test_reset_get(self):
        response = self.app.get(url(controller='account', action='do_reset',
                                    token='huhu',
                                    email='huhu@example.com'))
        assert '/login' in response.headers['location'], response.headers
        account = make_account()
        response = self.app.get(url(controller='account', action='do_reset',
                                    token=account.token,
                                    email=account.email))
        assert '/settings' in response.headers['location'], response.headers

    def test_completion_access_check(self):
        response = self.app.get(url(controller='account', action='complete'),
                                expect_errors=True)
        obj = json.loads(response.body)
        assert u'You are not authorized to see that page' == obj['errors']

    def test_distinct_json(self):
        test = make_account()
        response = self.app.get(url(controller='account', action='complete'),
                                extra_environ={'REMOTE_USER': str(test.name)})
        obj = json.loads(response.body)['results']
        assert obj[0].keys() == [u'fullname', u'name']
        assert len(obj) == 1, obj
        assert obj[0]['name'] == 'test', obj[0]

        response = self.app.get(url(controller='account', action='complete'),
                                params={'q': 'tes'},
                                extra_environ={'REMOTE_USER': str(test.name)})
        obj = json.loads(response.body)['results']
        assert len(obj) == 1, obj

        response = self.app.get(url(controller='account', action='complete'),
                                params={'q': 'foo'},
                                extra_environ={'REMOTE_USER': str(test.name)})
        obj = json.loads(response.body)['results']
        assert len(obj) == 0, obj

    def test_dashboard_not_logged_in(self):
        response = self.app.get(url(controller='account', action='dashboard'),
                                status=403)
        assert '403' in response.status, response.status

    def test_dashboard(self):
        test = make_account('test')
        cra = load_fixture('cra', manager=test)
        response = self.app.get(url(controller='account', action='dashboard'),
                                extra_environ={'REMOTE_USER': str(test.name)})
        assert '200' in response.status, response.status
        assert cra.label in response, response

    def test_profile(self):
        """
        Profile page test
        """

        # Create the test user account using default
        # username is test, fullname is 'Test User',
        # email is test@example.com and twitter handle is testuser
        test = make_account('test')

        # Get the user profile for an anonymous user
        response = self.app.get(url(controller='account', action='profile',
                                    name='test'))

        assert '200' in response.status, \
            'Profile not successfully returned for anonymous user'
        assert '<dt>Name</dt>' in response.body, \
            'Name heading is not in profile for anonymous user'
        assert '<dd>Test User</dd>' in response.body, \
            'User fullname is not in profile for anonymous user'
        assert '<dt>Username</dt>' in response.body, \
            'Username heading is not in profile for anonymous user'
        assert '<dd>test</dd>' in response.body, \
            'Username is not in profile for anonymous user'
        assert '<dt>Email</dt>' not in response.body, \
            'Email heading is in profile for anonymous user'
        assert '<dd>test@example.com</dd>' not in response.body, \
            'Email of user is in profile for anonymous user'
        assert '<dt>Twitter</dt>' not in response.body, \
            'Twitter heading is in profile for anonymous user'
        assert '<dd>@testuser</dd>' not in response.body, \
            'Twitter handle is in profile for anonymous user'

        # Display email and twitter handle for the user
        response = self.app.get(url(controller='account', action='profile',
                                    name='test'), extra_environ={'REMOTE_USER':
                                                                 'test'})

        assert '200' in response.status, \
            'Profile not successfully returned for user'
        assert '<dt>Email</dt>' in response.body, \
            'Email heading is not in profile for the user'
        assert '<dd>test@example.com</dd>' in response.body, \
            'Email of user is not in profile for the user'
        assert '<dt>Twitter</dt>' in response.body, \
            'Twitter heading is not in profile for the user'
        assert '@testuser' in response.body, \
            'Twitter handle of user is not in profile for the user'

        # Immitate that the user now makes email address and twitter handle
        # public to all
        test.public_email = True
        test.public_twitter = True
        db.session.add(test)
        db.session.commit()

        # Get the site as an anonymous user
        response = self.app.get(url(controller='account', action='profile',
                                    name='test'))

        assert '200' in response.status, \
            'Profile with public contact info not returned to anonymous user'
        assert '<dt>Email</dt>' in response.body, \
            'Public email heading not in profile for anonymous user'
        assert '<dd>test@example.com</dd>' in response.body, \
            'Public email not in profile for anonymous user'
        assert '<dt>Twitter</dt>' in response.body, \
            'Public Twitter heading not in profile for anonymous user'
        assert '@testuser' in response.body, \
            'Public Twitter handle not in profile for anonymous user'

        # We take it back and hide the email and the twitter handle
        test.public_email = False
        test.public_twitter = False
        db.session.add(test)
        db.session.commit()

        # Create admin user
        admin_user = make_account('admin', 'Admin', 'admin@os.com')
        admin_user.admin = True
        db.session.add(admin_user)
        db.session.commit()

        # Display email for admins
        response = self.app.get(url(controller='account', action='profile',
                                    name='test'), extra_environ={'REMOTE_USER':
                                                                 'admin'})

        assert '200' in response.status, \
            'Profile not successfully returned for admins'
        assert '<dt>Name</dt>' in response.body, \
            'Full name heading not in profile for admins'
        assert '<dd>Test User</dd>' in response.body, \
            'Full name of user not in profile for admins'
        assert '<dt>Username</dt>' in response.body, \
            'Username heading not in profile for admins'
        assert '<dd>test</dd>' in response.body, \
            'Username of user not in profile for admins'
        assert '<dt>Email</dt>' in response.body, \
            'Email heading not in profile for admins'
        assert '<dd>test@example.com</dd>' in response.body, \
            'Email of user not in profile for admins'
        assert '<dt>Twitter</dt>' in response.body, \
            'Twitter heading not in profile for admins'
        assert '@testuser' in response.body, \
            'Twitter handle of user not in profile for admins'

        # Do not display fullname if it's empty
        test.fullname = ''
        db.session.add(test)
        db.session.commit()

        response = self.app.get(url(controller='account', action='profile',
                                    name='test'))

        assert '200' in response.status, \
            'Profile page not successfully returned without full name'
        assert '<dt>Name</dt>' not in response.body, \
            'Name heading is in profile even though full name is empty'
        # Test if the information is missing or just the full name
        assert '<dt>Username</dt>' in response.body, \
            'Username heading is not in profile when full name is empty'
        assert '<dd>test</dd>' in response.body, \
            'Username for user is not in profile when full name is empty'

        # Do not display twitter handle if it's empty
        test.twitter_handle = None
        db.session.add(test)
        db.session.commit()

        response = self.app.get(url(controller='account', action='profile',
                                    name='test'), extra_environ={'REMOTE_USER':
                                                                 'test'})
        # Check if the Twitter heading is there
        assert '<dt>Twitter</dt>' not in response.body, \
            'Twitter heading is in profile even though twitter handle is empty'
        # Test if the other information is missing
        assert '<dt>Username</dt>' in response.body, \
            'Username heading is not in profile when Twitter handle is empty'
        assert '<dd>test</dd>' in response.body, \
            'Username for user is not in profile when Twitter handle is empty'

    def test_terms_check(self):
        """
        Test whether terms of use are present on the signup page (login) page
        and whether they are a required field.
        """

        # Get the login page
        response = self.app.get(url(controller='account', action='login'))
        assert '200' in response.status, \
            'Error (status is not 200) while retrieving the login/signup page'

        # Check if user can send an input field for terms of use/privacy
        assert 'name="terms"' in response.body, \
            'Terms of use input field not present'

        # Check whether the terms of use url is in the response
        # For now we rely on an external terms of use page and we therefore
        # check whether that page also exists.
        assert 'http://okfn.org/terms-of-use' in response.body, \
            'Terms of use url not in response'

        # Headers to immitate a browser
        headers = {'User-Agent': 'OpenSpending in-site browser',
                   'Accept': ','.join(['text/html', 'application/xhtml+xml',
                                       'application/xml;q=0.9', '*/*;q=0.8'])
                   }

        # We use urllib2 instead of webtest's get because of redirects
        request = urllib2.Request('http://okfn.org/terms-of-use',
                                  headers=headers)
        external_response = urllib2.urlopen(request)
        assert 200 == external_response.getcode(), \
            'External terms of use page not found'

        # Check whether the privay policy url is in the response
        # For now we rely on an external privacy policy and we therefore
        # check whether that page also exists.
        assert 'http://okfn.org/privacy-policy' in response.body, \
            'Privacy policy url not in response'

        request = urllib2.Request('http://okfn.org/privacy-policy',
                                  headers=headers)
        external_response = urllib2.urlopen(request)
        assert 200 == external_response.getcode(), \
            'External privacy policy page not found'

        # Check that not filling up the field throws a 'required' response
        # if the terms box is not in the post request (not checked)
        response = self.app.post(url(controller='account', action='register'),
                                 params={'name': 'termschecker',
                                         'fullname': 'Term Checker',
                                         'email': 'termchecker@test.com',
                                         'password1': 'secret',
                                         'password2': 'secret'})
        assert 'name="terms"' in response.body, \
            'Terms of use checkbox not present after registering without tick'
        # Check if user is told it is required (this can be anywhere on the
        # page, and might not even be tied to terms of use checkbox but it
        # should be present nonetheless)
        assert 'Required' in response.body, \
            'User is not told that a field is "Required"'

        # Check that terms input field is not present after a successful
        # register
        response = self.app.post(url(controller='account', action='register'),
                                 params={'name': 'termschecker',
                                         'fullname': 'Term Checker',
                                         'email': 'termchecker@test.com',
                                         'password1': 'secret',
                                         'password2': 'secret',
                                         'terms': True})
        assert 'name="terms"' not in response.body, \
            'Terms of use checkbox is present even after a successful register'

    def test_vary_header(self):
        """
        Test whether the Vary header is set to change on Cookies and whether
        the ETag gets a different value based on the cookies. This allows
        intermediate caches to serve different content based on whether the
        user is logged in or not
        """

        # We need to perform a get to get the cache settings from app globals
        response = self.app.get(url(controller='home', action='index'))

        # Get the cache settings from the app globals
        cache_settings = response.app_globals.cache_enabled
        # Enable cache
        response.app_globals.cache_enabled = True

        # Get the view page again (now with cache enabled)
        response = self.app.get(url(controller='home', action='index'))

        # Enforce check based on cookies
        assert 'Vary' in response.headers, \
            'Vary header is not present in response'
        assert 'Cookie' in response.headers.get('Vary'), \
            'Cookie is not in the vary header'

        # Save the ETag for an assertion
        etag_for_no_cookie = response.headers.get('etag')

        # Set a dummy login cookie
        self.app.cookies['openspending.login'] = 'testcookie'
        # Do a get (we don't need the remote user but let's try to immitate
        # a GET as closely as possible)
        response = self.app.get(url(controller='home', action='index'),
                                extra_environ={'REMOTE_USER': 'test'})

        # Get the ETag for the login cookie based GET
        etag_for_cookie = response.headers.get('etag')
        # Check if ETag is different in a login cookie based GET
        assert etag_for_cookie != etag_for_no_cookie, \
            'ETags for login cookie and no login cookie are the same'

        # Remove the login cookie from the cookiejar
        del self.app.cookies['openspending.login']

        # Reset cache setting
        response.app_globals.cache_enabled = cache_settings

    def test_user_scoreboard(self):
        """
        Test if the user scoreboard works and is only accessible by
        administrators
        """

        # Create dataset and users and make normal user owner of dataset
        admin_user = make_account('test_admin', admin=True)

        dataset = load_fixture('cra')
        normal_user = make_account('test_user')
        normal_user.datasets.append(dataset)
        db.session.add(normal_user)
        db.session.commit()

        # Refetch the accounts into scope after the commit
        admin_user = Account.by_name('test_admin')
        normal_user = Account.by_name('test_user')

        # Get the URL to user scoreboard
        scoreboard_url = url(controller='account', action='scoreboard')
        # Get the home page (could be just any page
        user_response = self.app.get(url(controller='home', action='index'),
                                     extra_environ={'REMOTE_USER':
                                                    str(normal_user.name)})
        admin_response = self.app.get(url(controller='home', action='index'),
                                      extra_environ={'REMOTE_USER':
                                                     str(admin_user.name)})

        # Admin user should be the only one to see a link
        # to the user scoreboard (not the normal user)
        assert scoreboard_url not in user_response.body, \
            "Normal user can see scoreboard url on the home page"

        assert scoreboard_url in admin_response.body, \
            "Admin user cannot see the scoreboard url on the home page"

        # Normal user should not be able to access the scoreboard url
        user_response = self.app.get(scoreboard_url,
                                     expect_errors=True,
                                     extra_environ={'REMOTE_USER':
                                                    str(normal_user.name)})
        assert '403' in user_response.status, \
            "Normal user is authorized to see user scoreboard"

        # Administrator should see scoreboard and users should be there in
        # in the following order normal user - admin user (with 10 and 0 points
        # respectively)
        admin_response = self.app.get(scoreboard_url,
                                      extra_environ={'REMOTE_USER':
                                                     str(admin_user.name)})

        assert '200' in admin_response.status, \
            "Administrator did not get a 200 status for user scoreboard"

        # We need to remove everything before an 'Dataset Maintainers' because
        # the admin user name comes first because of the navigational bar
        heading_index = admin_response.body.find('Dataset Maintainers')
        check_body = admin_response.body[heading_index:]

        admin_index = check_body.find(admin_user.name)
        user_index = check_body.find(normal_user.name)
        assert admin_index > user_index, \
            "Admin index comes before normal user index"

        # Same thing as with the username we check for the scores
        # they are represented as <p>10</p> and <p>0</p>
        admin_index = check_body.find('<p>0</p>')
        user_index = check_body.find('<p>10</p>')
        assert admin_index > user_index, \
            "Admin score does not come before the user score"
