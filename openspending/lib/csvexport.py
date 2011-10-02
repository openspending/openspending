import csv
import sys

from datetime import datetime
from StringIO import StringIO
from pylons.controllers.util import Response

from openspending import model
from openspending.mongo import DBRef, ObjectId

def write_csv(entries, response):
    response.content_type = 'text/csv'
    response.headers['Transfer-Encoding'] = 'chunked'
    return generate_csv(entries)

def generate_csv(entries):
    generate_headers = True
    for entry in entries:
        row = {}
        for k, v in model.entry.to_query_dict(entry).items():
            if isinstance(v, (list, tuple, dict, DBRef)):
                continue
            elif isinstance(v, ObjectId):
                v = str(v)
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
