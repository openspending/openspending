from openspending.model import Account
from openspending.test import DatabaseTestCase

def make_account():
    return Account(name='Joe Bloggs',
                   label='Tester',
                   email='joe.bloggs@example.com')

class TestAccount(DatabaseTestCase):

    def setup(self):
        super(TestAccount, self).setup()
        self.acc = make_account()
        self.acc.save()

    def test_account_properties(self):
        assert self.acc.name == 'Joe Bloggs'
        assert self.acc.email == 'joe.bloggs@example.com'
        assert self.acc.label == 'Tester'

    def test_account_api_key(self):
        assert len(self.acc.api_key) == 36

    def test_account_lookup_by_name(self):
        res = Account.by_name('Joe Bloggs')
        assert res == self.acc

    def test_account_lookup_by_api_key(self):
        res = Account.by_api_key(self.acc.api_key)
        assert res == self.acc
