from .. import ControllerTestCase, url, helpers as h
from openspending.model import Account, meta as db
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

    def test_distinct_json(self):
        h.make_account()
        response = self.app.get(url(controller='account', action='complete'),
                                params={})
        obj = json.loads(response.body)['results']
        assert len(obj) == 1, obj
        assert obj[0]['name'] == 'test', obj[0]

        response = self.app.get(url(controller='account', action='complete'),
                                params={'q': 'tes'})
        obj = json.loads(response.body)['results']
        assert len(obj) == 1, obj

        response = self.app.get(url(controller='account', action='complete'),
                                params={'q': 'foo'})
        obj = json.loads(response.body)['results']
        assert len(obj) == 0, obj