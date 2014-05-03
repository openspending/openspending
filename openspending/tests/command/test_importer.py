from openspending.model.account import Account
from openspending.model import meta as db
from openspending.command.importer import shell_account

from openspending.tests.base import TestCase
from mock import patch


class TestImporter(TestCase):

    @patch.object(Account, 'by_name', return_value='the account')
    def test_shell_account_when_it_exists(self, account_mock):
        assert shell_account() == 'the account'
        Account.by_name.assert_called_once_with('system')

    @patch.object(Account, 'by_name', return_value=None)
    def test_shell_account_when_it_doesnt_exists(self, account_mock):
        with patch.object(db, 'session'):
            account = shell_account()
            assert account.name == 'system'
            db.session.add.assert_called_once_with(account)
