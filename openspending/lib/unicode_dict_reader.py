# work around python2's csv.py's difficulty with utf8
# partly cribbed from http://stackoverflow.com/questions/5478659/python-module-like-csv-dictreader-with-full-utf8-support

class EmptyCSVError(Exception):
    pass

def UnicodeDictReader(file_or_str, encoding='utf8', **kwargs):
    import csv

    def decode(s, encoding):
        if s is None:
            return None
        return s.decode(encoding)

    csv_reader = csv.DictReader(file_or_str, **kwargs)

    if not csv_reader.fieldnames:
        raise EmptyCSVError("No fieldnames in CSV reader: empty file?")

    keymap = dict((k, k.decode(encoding)) for k in csv_reader.fieldnames)
    for row in csv_reader:
        yield dict((keymap[k], decode(v, encoding)) for k, v in row.iteritems())
