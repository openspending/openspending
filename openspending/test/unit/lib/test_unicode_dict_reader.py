from openspending.lib import unicode_dict_reader as udr

from ... import TestCase, helpers as h

class TestUnicodeDictReader(TestCase):
    def test_reads_simple_csv(self):
        reader = udr.UnicodeDictReader(h.fixture_file('simple.csv'))
        lines = [ l for l in reader ]

        h.assert_equal(lines[0], {'a': '1', 'b': '2', 'c': 'foo'})
        h.assert_equal(lines[1], {'a': '3', 'b': '4', 'c': 'bar'})

    def test_reads_unicode(self):
        reader = udr.UnicodeDictReader(h.fixture_file('simple.csv'))
        lines = [ l for l in reader ]

        h.assert_true(isinstance(lines[0].keys()[0], unicode),
                      "Keys in UnicodeDictReader dicts should be unicode.")
        h.assert_true(isinstance(lines[0].values()[0], unicode),
                      "Values in UnicodeDictReader dicts should be unicode.")

    @h.raises(udr.EmptyCSVError)
    def test_raises_on_empty_csv(self):
        reader = udr.UnicodeDictReader(h.fixture_file('empty.csv'))
        lines = [ l for l in reader ]
