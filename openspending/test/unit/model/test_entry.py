from openspending.model import Entry
from openspending.test import DatabaseTestCase, helpers as h

def make_entry():
    return Entry(name='testentry',
                 label='An Entry',
                 amount=123.45,
                 currency='GBP')

class TestEntry(DatabaseTestCase):

    def setup(self):
        super(TestEntry, self).setup()
        self.ent = make_entry()
        self.ent.save()

    def test_entry_properties(self):
        h.assert_equal(self.ent.name, 'testentry')
        h.assert_equal(self.ent.label, 'An Entry')
        h.assert_equal(self.ent.amount, 123.45)
        h.assert_equal(self.ent.currency, 'GBP')

