'''\
Helper methods for using Solr.
'''

import logging
from datetime import datetime
from dateutil import tz
from unicodedata import category

from solr import SolrConnection

from openspending import model
from openspending.lib.util import flatten
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import ISolrSearch

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
    drop('dataset:%s' % dataset_name)

def drop(query):
    solr = get_connection()
    solr.delete_query(query)
    solr.commit()

SOLR_CORE_FIELDS = ['id', 'dataset', 'amount', 'time', 'location', 'from',
                    'to', 'notes']

def safe_unicode(s):
    if not isinstance(s, basestring):
        return s
    return u"".join([c for c in unicode(s) if not category(c)[0] == 'C'])



def extend_entry(entry, dataset):
    entry['dataset'] = dataset.data.get('dataset', {})
    entry = flatten(entry)
    entry['_id'] = dataset.name + '::' + unicode(entry['id'])
    for k, v in entry.items():
        # this is similar to json encoding, but not the same.
        if isinstance(v, datetime) and not v.tzinfo:
            entry[k] = datetime(v.year, v.month, v.day, v.hour,
                                v.minute, v.second, tzinfo=tz.tzutc())
        elif '.' in k and isinstance(v, (list, tuple)):
            entry[k] = " ".join([unicode(vi) for vi in v])
        else:
            entry[k] = safe_unicode(entry[k])
        if k.endswith(".name"):
            vk = k[:len(k)-len(".name")]
            entry[vk] = v
        if k.endswith(".label"):
            entry[k + "_str"] = entry[k]
            entry[k + "_facet"] = entry[k]
    for item in PluginImplementations(ISolrSearch):
        entry = item.update_index(entry)
    return entry

def optimize():
    solr = get_connection()
    solr.optimize()
    solr.commit()

def build_index(dataset_name):
    solr = get_connection()
    dataset_ = model.Dataset.by_name(dataset_name)
    assert dataset_ is not None, "No such dataset: %s" % dataset_name
    buf = []
    total = 0
    increment = 500
    for entry in dataset_.materialize():
        ourdata = extend_entry(entry, dataset_)
        buf.append(ourdata)
        if len(buf) == increment:
            solr.add_many(buf)
            solr.commit()
            total += increment
            log.info("Indexed %d entries", total)
            buf = []
    solr.add_many(buf)
    solr.commit()
