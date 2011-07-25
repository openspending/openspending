from openspending.model import Dataset
from openspending.test import DatabaseTestCase, helpers as h

class MockEntry(dict):
    name = "testentry"
    label = "An Entry"

    def __init__(self):
        self['name'] = self.name
        self['label'] = self.label

def make_dataset():
    return Dataset(name='testdataset')

class TestDataset(DatabaseTestCase):

    def setup(self):
        super(TestDataset, self).setup()
        self.dat = make_dataset()
        self.dat.save()

    def test_dataset_properties(self):
        assert self.dat.name == 'testdataset'

    def test_get_regions(self):
        assert self.dat.get_regions() == []

    def test_add_region(self):
        self.dat.add_region("region 1")
        assert self.dat.get_regions() == ["region 1"]

    def test_add_region_ignores_duplicates(self):
        self.dat.add_region("region 1")
        self.dat.add_region("region 1")
        assert self.dat.get_regions() == ["region 1"]

    def test_distinct_regions(self):
        b = make_dataset()
        self.dat.add_region("region 1")
        self.dat.add_region("region 2")
        b.add_region("region 1")
        self.dat.save()
        b.save()

        assert Dataset.distinct_regions() == ["region 1", "region 2"]

    def test_find_by_region(self):
        self.dat.add_region("region 1")
        self.dat.save()

        assert Dataset.find_by_region("region 1").next() == self.dat

    def test_entry_custom_html(self):
        assert self.dat.entry_custom_html is None
        self.dat.entry_custom_html = '<span>custom html</span>'
        self.dat.save()

        assert Dataset.find_one().entry_custom_html == '<span>custom html</span>'

    def test_render_entry_custom_html_none(self):
        h.assert_equal(self.dat.render_entry_custom_html(MockEntry()), None)

    def test_render_entry_custom_html_plain_text(self):
        self.dat.entry_custom_html = 'No templating.'
        self.dat.save()
        h.assert_equal(self.dat.render_entry_custom_html(MockEntry()),
                       'No templating.')

    def test_render_entry_custom_html_genshi_template(self):
        self.dat.entry_custom_html='${entry.name}: ${entry.label}'
        self.dat.save()
        h.assert_equal(self.dat.render_entry_custom_html(MockEntry()),
                       'testentry: An Entry')
