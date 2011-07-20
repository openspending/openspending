import csv

from datetime import datetime
from bson.dbref import DBRef
from bson.objectid import ObjectId

def write_csv(entries, response):
    response.content_type = 'text/csv'

    # NOTE: this should be a streaming service but currently
    # I see no way to know the full set of keys without going
    # through the data twice.
    keys = set()
    rows = []
    for entry in entries:
        d = {}
        for k, v in entry.to_query_dict().items():
            if isinstance(v, (list, tuple, dict, DBRef)):
                continue
            elif isinstance(v, ObjectId):
                v = str(v)
            elif isinstance(v, datetime):
                v = v.isoformat()
            d[k] = unicode(v).encode('utf-8')
        keys.update(d.keys())
        rows.append(d)

    writer = csv.DictWriter(response, sorted(keys), dialect='excel',
                            delimiter=',')
    writer.writerow(dict(zip(keys, keys)))
    writer.writerows(rows)
