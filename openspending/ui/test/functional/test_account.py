from .. import ControllerTestCase, url, helpers as h
from openspending.model import Account, meta as db
from openspending.lib.mailer import MailerException
from pylons import config
import json


class TestAccountController(ControllerTestCase):

    def test_login(self):
        response = self.app.get(url(controller='account', action='login'))

    def test_register(self):
        response = self.app.get(url(controller='account', action='register'))

    @h.patch('openspending.auth.account.update')
    @h.patch('openspending.ui.lib.base.model.Account.by_name')
    def test_settings(self, model_mock, update_mock):
        account = Account()
        account.name = 'mockaccount'
        db.session.add(account)
        db.session.commit()
        model_mock.return_value = account
        update_mock.return_value = True
        response = self.app.get(url(controller='account', action='settings'),
                                extra_environ={'REMOTE_USER': 'mockaccount'})

    def test_after_login(self):
        response = self.app.get(url(controller='account', action='after_login'))

    def test_after_logout(self):
        response = self.app.get(url(controller='account', action='after_logout'))

    def test_trigger_reset_get(self):
        response = self.app.get(url(controller='account', action='trigger_reset'))
        assert 'email address you used to register your account' in response.body, response.body

    def test_trigger_reset_post_fail(self):
        response = self.app.post(url(controller='account', action='trigger_reset'),
                params={'emailx': "foo@bar"})
        assert 'Please enter an email address' in response.body, response.body
        response = self.app.post(url(controller='account', action='trigger_reset'),
                params={'email': "foo@bar"})
        assert 'No user is registered' in response.body, response.body

    @h.raises(MailerException)
    def test_trigger_reset_post_ok(self):
        try:
            original_smtp_server = config.get('smtp_server')
            config['smtp_server'] = 'non-existent-smtp-server'
            account = h.make_account()
            response = self.app.post(url(controller='account', action='trigger_reset'),
                    params={'email': "test@example.com"})
        finally:
            config['smtp_server'] = original_smtp_server

    def test_reset_get(self):
        response = self.app.get(url(controller='account', action='do_reset',
                                    token='huhu',
                                    email='huhu@example.com'))
        assert '/login' in response.headers['location'], response.headers
        account = h.make_account()
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
        test = h.make_account()
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
        test = h.make_account('test')
        cra = h.load_fixture('cra', manager=test)
        response = self.app.get(url(controller='account', action='dashboard'),
                                extra_environ={'REMOTE_USER': str(test.name)})
        assert '200' in response.status, response.status
        assert cra.label in response, response

    def test_profile(self):
        # Test the profile page
        test = h.make_account('test')
        response = self.app.get(url(controller='account', action='profile',
                                name='test'))
        assert '<dt>Name</dt>' in response.body
        assert '<dd>Test User</dd>' in response.body
        assert '<dt>Username</dt>' in response.body
        assert '<dd>test</dd>' in response.body
        assert '<dt>Email</dt>' not in response.body
        assert '<dd>test@example.com</dd>' not in response.body
        assert '200' in response.status

        admin_user = h.make_account('admin', 'Admin', 'admin@os.com')
        admin_user.admin = True
        db.session.add(admin_user)
        db.session.commit()

        # Display email for admins
        response = self.app.get(url(controller='account', action='profile',
                                name='test'), extra_environ={'REMOTE_USER':
                                                             'admin'})
        assert '<dt>Name</dt>' in response.body
        assert '<dd>Test User</dd>' in response.body
        assert '<dt>Username</dt>' in response.body
        assert '<dd>test</dd>' in response.body
        assert '<dt>Email</dt>' in response.body
        assert '<dd>test@example.com</dd>' in response.body
        assert '200' in response.status

        # Do not display fullname if it's empty
        test.fullname = ''
        db.session.add(test)
        db.session.commit()
        response = self.app.get(url(controller='account', action='profile',
                                name='test'))
        assert '<dt>Username</dt>' in response.body
        assert '<dd>test</dd>' in response.body
        assert '<dt>Email</dt>' not in response.body
        assert '<dd>test@example.com</dd>' not in response.body
        assert '200' in response.status

    def test_terms_check(self):
        # Check that the field is displayed
        response = self.app.get(url(controller='account', action='login'))
        assert '200' in response.status
        assert ('I agree to the <a href="okfn.org/terms-of-use/">Terms of '
                'Use</a> and <a href="http://okfn.org/privacy-policy/">Privacy'
                ' Policy</a>' in response)

        # Check that not filling up the field throws a response
        response = self.app.post(url(controller='account', action='register'))
        assert ('<input name="terms" type="checkbox" /> <p class="help-block '
                'error">Required</p>' in response)
