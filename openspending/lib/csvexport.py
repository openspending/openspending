import csv

from datetime import datetime
from StringIO import StringIO

from openspending.lib.util import flatten


def write_csv(entries, response, filename=None):
    csv_headers(response, filename)
    return generate_csv(entries)


def csv_headers(response, filename='download.csv'):
    response.content_type = 'text/csv'
    if filename:
        response.content_disposition = 'attachment; filename=%s' % filename


def generate_csv(entries, generate_headers=True):
    for entry in entries:
        yield generate_csv_row(entry, generate_headers)
        generate_headers = False


def generate_csv_row(entry, generate_headers=True):
    row = {}
    for k, v in flatten(entry).items():
        if isinstance(v, (list, tuple, dict)):
            continue
        elif isinstance(v, datetime):
            v = v.isoformat()
        elif isinstance(v, float):
            v = u'%.2f' % v
        row[unicode(k).encode('utf8')] = unicode(v).encode('utf8')

    fields = sorted(row.keys())
    sio = StringIO()
    writer = csv.DictWriter(sio, fields)
    if generate_headers:
        header = dict(zip(fields, fields))
        writer.writerow(header)

    writer.writerow(row)
    return sio.getvalue()
