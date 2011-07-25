'''\
Helper methods for using Solr.
'''

import logging
from datetime import datetime
from dateutil import tz
from unicodedata import category

from bson.dbref import DBRef
from pymongo.objectid import ObjectId
from solr import SolrConnection

from openspending import model
from openspending.plugins import PluginImplementations, ISolrSearch

log = logging.getLogger(__name__)

url = 'http://localhost:8983/solr'
http_user = None
http_pass = None

_client = None

def configure(config=None):
    global url
    global http_user
    global http_pass

    if not config:
        config = {}

    url = config.get('openspending.solr.url', url)
    http_user = config.get('openspending.solr.http_user', http_user)
    http_pass = config.get('openspending.solr.http_pass', http_pass)

# Solr connection singleton
_solr = None

def get_connection():
    """Returns the global Solr connection, or creates one, as required."""
    global _solr

    if _solr:
        return _solr

    if url == 'stub':
        _solr = _Stub()
    else:
        _solr = SolrConnection(url,
                               http_user=http_user,
                               http_pass=http_pass)

    return _solr


# TODO: this should move in openspending.ui/tests/stub/solr.py or the like
class _Stub(object):
    '''
    Fakes the API of solrpy, to avoid needing a real instance of SOLR for
    testing.
    '''
    def __init__(self):
        self.records = []
        self.results = []

    def add(self, **kwargs):
        self.records.append(kwargs)

    def add_many(self, records):
        self.records = self.records + records

    def commit(self):
        pass

    def optimize(self):
        pass

    def delete_query(self, q, **kwargs):
        self.records = []
        pass

    def query(self, q, **kwargs):
        if q == '*' or q == '':
            self.results = self.records
        else:
            def match(query, rec):
                for v in rec.values():
                    if query in unicode(v):
                        return True
            self.results = [r for r in self.records if match(q, r)]
        return self

    @property
    def numFound(self):
        return len(self.results)

def drop_index(dataset_name):
    solr = get_connection()
    solr.delete_query('dataset:%s' % dataset_name)
    solr.commit()

SOLR_CORE_FIELDS = ['id', 'dataset', 'amount', 'time', 'location', 'from',
                    'to', 'notes']

def safe_unicode(s):
    if not isinstance(s, basestring):
        return s
    return u"".join([c for c in unicode(s) if not category(c) == 'Cc'])


def extend_entry(entry):
    entry = entry.to_index_dict()
    for k, v in entry.items():
        # this is similar to json encoding, but not the same.
        if isinstance(v, DBRef):
            del entry[k]
        elif isinstance(v, ObjectId):
            entry[k] = str(v)
        elif isinstance(v, datetime) and not v.tzinfo:
            entry[k] = datetime(v.year, v.month, v.day, v.hour,
                                v.minute, v.second, tzinfo=tz.tzutc())
        elif '.' in k and isinstance(v, (list, tuple)):
            entry[k] = " ".join([unicode(vi) for vi in v])
        else:
            entry[k] = safe_unicode(entry[k])
        if k.endswith(".label") or k.endswith(".name"):
            entry[k + "_str"] = entry[k]
            entry[k + "_facet"] = entry[k]
    if 'classifiers' in entry:
        entry['classifiers'] = map(str, entry['classifiers'])
    if 'entities' in entry:
        entry['entities'] = map(str, entry['entities'])
    for item in PluginImplementations(ISolrSearch):
        entry = item.update_index(entry)
    return entry


def optimize():
    solr = get_connection()
    solr.optimize()
    solr.commit()

def build_index(dataset_name=None):
    solr = get_connection()
    query = {}
    if dataset_name:
        dataset_ = model.Dataset.find_one({'name': dataset_name})
        assert dataset_ is not None, "No such dataset: %s" % dataset_name
        query = {'dataset.name': dataset_name}
    cur = model.Entry.find(query)
    buf = []
    total = 0
    increment = 500
    for entry in cur:
        ourdata = extend_entry(entry)
        buf.append(ourdata)
        if len(buf) == increment:
            solr.add_many(buf)
            solr.commit()
            total += increment
            log.info("Indexed %d entries", total)
            buf = []
    solr.add_many(buf)
    solr.commit()