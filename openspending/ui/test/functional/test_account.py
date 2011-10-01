from .. import ControllerTestCase, url, helpers as h

class TestAccountController(ControllerTestCase):

    def test_login(self):
        response = self.app.get(url(controller='account', action='login'))

    def test_register(self):
        response = self.app.get(url(controller='account', action='register'))

    @h.patch('openspending.ui.lib.authz.have_role')
    @h.patch('openspending.ui.lib.base.model.account.find_one_by')
    def test_settings(self, model_mock, have_role_mock):
        model_mock.return_value = {'name': 'mockaccount'}
        have_role_mock.return_value = True
        response = self.app.get(url(controller='account', action='settings'),
                                extra_environ={'REMOTE_USER': 'mockaccount'})

    def test_after_login(self):
        response = self.app.get(url(controller='account', action='after_login'))

    def test_after_logout(self):
        response = self.app.get(url(controller='account', action='after_logout'))