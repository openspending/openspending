import csv
import sys

from datetime import datetime

from openspending import model
from openspending.mongo import DBRef, ObjectId

def write_csv(entries, response):
    response.content_type = 'text/csv'

    # NOTE: this should be a streaming service but currently
    # I see no way to know the full set of keys without going
    # through the data twice.
    keys = set()
    rows = []
    for entry in entries:
        d = {}
        for k, v in model.entry.to_query_dict(entry).items():
            if isinstance(v, (list, tuple, dict, DBRef)):
                continue
            elif isinstance(v, ObjectId):
                v = str(v)
            elif isinstance(v, datetime):
                v = v.isoformat()
            d[unicode(k).encode('utf8')] = unicode(v).encode('utf8')
        keys.update(d.keys())
        rows.append(d)

    fields = sorted(keys)
    writer = csv.DictWriter(response, fields)

    if sys.version_info < (2,7):
        header = dict(zip(fields, fields))
        writer.writerow(header)
    else:
        writer.writeheader()

    writer.writerows(rows)
