import csv

from datetime import datetime
from StringIO import StringIO

from openspending.lib.util import flatten

def write_csv(entries, response, filename=None):
    response.content_type = 'text/csv'
    if filename:
        response.content_disposition = 'attachment; filename=%s' % filename
    return generate_csv(entries)

def generate_csv(entries):
    generate_headers = True
    for entry in entries:
        row = {}
        for k, v in flatten(entry).items():
            if isinstance(v, (list, tuple, dict)):
                continue
            elif isinstance(v, datetime):
                v = v.isoformat()
            row[unicode(k).encode('utf8')] = unicode(v).encode('utf8')

        fields = sorted(row.keys())
        sio = StringIO()
        writer = csv.DictWriter(sio, fields)

        if generate_headers:
            header = dict(zip(fields, fields))
            writer.writerow(header)
            generate_headers = False

        writer.writerow(row)
        yield sio.getvalue()
