import json
from collections import defaultdict

from openspending import model
from openspending.lib import solr_util as solr

class Browser(object):

    def __init__(self,
                 q='',
                 filter=None,
                 page=1,
                 pagesize=100,
                 facet_field=None,
                 facet_page=1,
                 facet_pagesize=100):

        self.params = {
            'q': q,
            'filter': filter if filter is not None else {},
            'page': page,
            'pagesize': pagesize,
            'facet_field': facet_field if facet_field is not None else [],
            'facet_page': facet_page,
            'facet_pagesize': facet_pagesize
        }

    def execute(self):
        """
        Run the query for this browser instance.

        Returns a tuple of dicts: (stats, facets, entries)
        """
        q = self.query()

        stats = {
            'results_count_query': q['response']['numFound'],
            'results_count': len(q['response']['docs'])
        }

        facets = q.get('facet_counts', {}).get('facet_fields', {})
        for k in facets.keys():
            facets[k] = _parse_facets(facets[k])

        entries = _get_entries(q['response']['docs'])

        return stats, facets, entries

    def query(self):
        data = solr.get_connection().raw_query(**_build_query(self.params))
        return json.loads(data)

def _build_query(params):
    filters = params['filter'].copy()

    query = {
        'q':     params['q'] or '*:*',
        'fq':    _build_fq(filters),
        'wt':    'json',
        'fl':    'id, dataset',
        'sort':  'score desc, amount desc',
        # FIXME: In a future version of the API, we really should use
        #        offset/limit rather than page/pagesize.
        'start': (params['page'] - 1) * params['pagesize'],
        'rows':  params['pagesize'],
    }
    if params['facet_field']:
        query.update({
            'facet': 'true',
            'facet.field': params['facet_field'],
            'facet.mincount': 1,
            'facet.sort': 'count',
            'facet.offset': (params['facet_page'] - 1) * params['facet_pagesize'],
            'facet.limit': params['facet_pagesize']
        })
    return query

def _build_fq(filters):
    """
    Make a Solr 'fq' object from a filters dict.

    Returns a list, suitable for passing as the 'fq' keyword argument to ``raw_query()``
    """
    def fq_for(key, value):
        return "+%s:\"%s\"" % (key, value.replace('"', '\\"'))
    fq = []
    for key, value in filters.iteritems():
        if isinstance(value, basestring):
            fq.append(fq_for(key, value))
        else:
            fq.append(' OR '.join(map(lambda v: fq_for(key, v), value)))
    return fq

def _parse_facets(facets):
    out = []

    for i in xrange(0, len(facets), 2):
        out.append([facets[i], facets[i+1]])

    return out

def _get_entries(docs):
    # Make a mapping between id and original index, to preserve
    # the results order
    ids_map = dict((d['id'], idx) for idx, d in enumerate(docs))

    # partition the entries by dataset (so we make only N queries
    # for N datasets)
    by_dataset = defaultdict(list)
    for d in docs:
        by_dataset[d['dataset']].append(d['id'])

    # create a great big list of entries, one per doc
    entries = []
    for ds_name, ids in by_dataset.iteritems():
        dataset = model.Dataset.by_name(ds_name)
        query = dataset.alias.c.id.in_(ids)
        entries.extend(dataset.entries(query))

    # shuffle these entries back into the correct order
    entries_ordered = [None] * len(entries)
    for entry in entries:
        entries_ordered[ids_map[entry['id']]] = entry

    for entry in entries_ordered:
        yield entry
