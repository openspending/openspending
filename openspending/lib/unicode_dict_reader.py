# work around python2's csv.py's difficulty with utf8
# partly cribbed from http://stackoverflow.com/questions/5478659/python-module-like-csv-dictreader-with-full-utf8-support

import csv

class EmptyCSVError(Exception):
    pass


class UnicodeDictReader(object):
    def __init__(self, fp, encoding='utf8', **kwargs):
        self.encoding = encoding
        self.reader = csv.DictReader(fp, **kwargs)

        if not self.reader.fieldnames:
            raise EmptyCSVError("No fieldnames in CSV reader: empty file?")

        self.keymap = dict((k, k.decode(encoding)) for k in self.reader.fieldnames)

    def __iter__(self):
        return (self._decode_row(row) for row in self.reader)

    def _decode_row(self, row):
        return dict(
            (self.keymap[k], self._decode_str(v)) for k, v in row.iteritems()
        )

    def _decode_str(self, s):
        if s is None:
            return None
        return s.decode(self.encoding)
