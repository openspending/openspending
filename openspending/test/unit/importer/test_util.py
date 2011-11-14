from StringIO import StringIO

from openspending.importer import util

from ... import TestCase, helpers as h

@h.patch('openspending.importer.util.urlopen')
def test_urlopen_lines(urlopen_mock):
    urlopen_mock.return_value = StringIO("line one\nline two\r\nline three")

    lines = [line for line in util.urlopen_lines("http://none")]

    h.assert_equal(lines,
                   ["line one\n", "line two\n", "line three"])
