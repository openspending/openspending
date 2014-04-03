from openspending import model

from ... import DatabaseTestCase, helpers as h


def make_account():
    return {
        'name': 'Joe Bloggs',
        'label': 'Tester',
        'email': 'joe.bloggs@example.com'
    }


class TestAccount(DatabaseTestCase):

    @h.skip
    def test_account_create_gives_api_key(self):
        account = model.account.create(make_account())
        h.assert_equal(len(account['api_key']), 36)

    @h.skip
    def test_account_add_role(self):
        account = model.account.create(make_account())
        model.account.add_role(account, 'admin')
        account = model.account.get(account['_id'])
        h.assert_equal(account['roles'], ['admin'])
