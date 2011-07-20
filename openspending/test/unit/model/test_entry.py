from openspending.model import Entry, Dataset
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

    def test_entry_custom_html_none(self):
        self.ent.dataset = Dataset()
        self.ent.dataset.save()
        h.assert_equal(self.ent.render_custom_html(), None)

    def test_entry_custom_html_plain_text(self):
        self.ent.dataset = Dataset(entry_custom_html='No templating.')
        self.ent.dataset.save()
        h.assert_equal(self.ent.render_custom_html(), 'No templating.')

    def test_entry_custom_html_genshi_template(self):
        self.ent.dataset = Dataset(entry_custom_html='${entry.name}: ${entry.label}')
        self.ent.dataset.save()
        h.assert_equal(self.ent.render_custom_html(), 'testentry: An Entry')

    def test_entry_custom_html_fetches_right_dataset(self):
        ds = [ Dataset(name=str(x), entry_custom_html=str(x)) for x in range(3) ]

        for d in ds:
            d.save()

        self.ent.dataset = ds[1]
        self.ent.dataset.save()

        h.assert_equal(self.ent.render_custom_html(), '1')

