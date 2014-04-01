import json
from collections import defaultdict

from openspending import model
from openspending.lib import solr_util as solr
from openspending.lib import util


class Browser(object):

    def __init__(self,
                 q='',
                 filter=None,
                 page=1,
                 pagesize=100,
                 order=None,
                 stats=False,
                 facet_field=None,
                 facet_page=1,
                 facet_pagesize=100):

        self.params = {
            'q': q,
            'filter': filter if filter is not None else {},
            'page': page,
            'pagesize': pagesize,
            'order': order if order is not None else [('score', True), ('amount', True)],
            'stats': stats,
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

        self.stats = {
            'results_count_query': q['response']['numFound'],
            'results_count': len(q['response']['docs'])
        }

        if self.params['stats']:
            self.stats.update(q.get('stats', {}).get('stats_fields', {}).
                              get('amount', {}))

        self.facets = q.get('facet_counts', {}).get('facet_fields', {})
        for k in self.facets.keys():
            self.facets[k] = _parse_facets(self.facets[k])

        self.entries = _get_entries(q['response']['docs'])

    def get_stats(self):
        return self.stats

    def get_facets(self):
        return self.facets

    def get_expanded_facets(self, dataset):
        return util.expand_facets(self.facets, dataset)

    def get_entries(self):
        return self.entries

    def query(self):
        data = solr.get_connection().raw_query(**_build_query(self.params))
        return json.loads(data)


def _build_query(params):
    query = {
        'q': params['q'] or '*:*',
        'fq': _build_fq(params['filter']),
        'wt': 'json',
        'fl': 'id, dataset',
        'sort': _build_sort(params['order']),
        'stats': str(params['stats']).lower(),
        'stats.field': 'amount',
        # FIXME: In a future version of the API, we really should use
        #        offset/limit rather than page/pagesize.
        #
        # NB: we permit fractional page sizes to overcome the limits of
        # page/pagesize vs offset/limit
        'start': int((params['page'] - 1) * params['pagesize']),
        'rows': params['pagesize'],
    }
    if params['facet_field']:
        query.update({
            'facet': 'true',
            'facet.field': params['facet_field'],
            'facet.mincount': 1,
            'facet.sort': 'count',
            # NB: we permit fractional page sizes to overcome the limits of
            # page/pagesize vs offset/limit
            'facet.offset': int((params['facet_page'] - 1)
                                * params['facet_pagesize']),
            'facet.limit': params['facet_pagesize']
        })
    return query


def _build_fq(filters):
    """
    Make a Solr 'fq' object from a filters dict.

    Returns a list, suitable for passing as the 'fq' keyword
    argument to ``raw_query()``
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


def _build_sort(order):
    sort = []
    for field, reverse in order:
        sort.append('{0} {1}'.format(field, 'desc' if reverse else 'asc'))
    return ', '.join(sort)


def _parse_facets(facets):
    out = []

    for i in xrange(0, len(facets), 2):
        out.append([facets[i], facets[i + 1]])

    return out


def _get_entries(docs):
    # List of ids in Solr return order
    # print [docs]
    ids = [d['id'] for d in docs]

    # partition the entries by dataset (so we make only N queries
    # for N datasets)
    by_dataset = defaultdict(list)
    for d in docs:
        by_dataset[d['dataset']].append(d['id'])

    # create a great big list of entries, one per doc
    entries = []
    for ds_name, ds_ids in by_dataset.iteritems():
        dataset = model.Dataset.by_name(ds_name)
        query = dataset.alias.c.id.in_(ds_ids)
        entries.extend([(dataset, e) for e in dataset.entries(query)])

    entries = util.sort_by_reference(ids, entries, lambda x: x[1]['id'])
    for dataset, entry in entries:
        yield dataset, entry
