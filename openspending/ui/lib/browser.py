from itertools import izip_longest, count
from urllib import urlencode

from pylons import response

from openspending.lib import json
from openspending.lib import solr_util as solr
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_browser_json
from openspending.ui.lib.page import Page

FILTER_PREFIX = "filter-"
DIMENSION_LABEL = ".label_facet"

STREAM_BATCH_SIZE = 1000
PAGE_SIZE = 50 # Applies only to HTML output, not CSV or JSON

class Browser(object):

    def __init__(self, dataset, args, url=None):
        self.args = args
        self.url = url
        self.dataset = dataset

        self._results = None
        self._page = None
        self.facets = []
        self.solr_args = {}
        self._filters = []

        self._set_limit()
        self._set_page_number()

    @property
    def filters(self):
        filters = []
        for k, v in self.args.items():
            if k.startswith(FILTER_PREFIX):
                k = k[len(FILTER_PREFIX):]
                filters.append((k, v))
        return filters

    def filter_by(self, *fq):
        self._filters.extend(fq)

    def _set_limit(self, limit=PAGE_SIZE):
        # set limit to be the value of the limit query
        # param, unless no such query param is set.
        try:
            self.limit = int(self.args.get('limit'))
        except TypeError:
            self.limit = limit

    def _set_page_number(self):
        try:
            self.page_number = int(self.args.get('page'))
        except TypeError:
            self.page_number = 1

    @property
    def start(self):
        return (self.page_number - 1) * self.limit

    @property
    def fq(self):
        filters = []
        filters.extend(self._filters)
        if self.dataset is not None:
            filters.append("+dataset:%s" % self.dataset.name)
        for field, value in self.filters:
            filters.append("+%s:\"%s\"" % (field, 
                value.replace('"', '\\"')))
        return filters

    def facet_name(self, facet):
        facet = facet.replace(DIMENSION_LABEL, "")
        if not len(facet):
            return "(Unknown)"
        for dimension in self.dataset.dimensions:
            if dimension.name == facet:
                return dimension.label or facet
        return facet.capitalize().replace("_", " ")

    def facet_by_dimensions(self):
        for dimension in self.dataset.dimensions:
            key = dimension.name
            if dimension.type != 'value':
                key += DIMENSION_LABEL
            if dimension.facet:
                self.facets.append(key)

    def facet_by(self, *facets):
        self.facets.extend(facets)

    def apply(self, **kwargs):
        self.solr_args.update(kwargs)

    @property
    def q(self):
        return self.args.get('q', '')

    @property
    def results(self):
        if self._results is None:
            self._results = self.query()
        return self._results

    @property
    def items(self):
        return self.results.get('response', {}).get('docs')

    @property
    def num_results(self):
        return self.results.get('response', {}).get('numFound')

    def facet_values(self, name):
        values = self.results.get('facet_counts', {}).get('facet_fields',
                {}).get(name, [])
        options = []
        for value in values[::2]:
            count_ = values[values.index(value)+1]
            options.append((value, count_))
        return dict(options)

    @property
    def stats(self):
        return {} #self.results.get('stats').get('stats_fields').get('amount')

    @property
    def page(self):
        if self._page is None:
            def _url(page, **kwargs):
                return self.state_url(('page', unicode(page)),
                                      ('page', unicode(self.page_number)))
            self._page = Page(
                list(self.entries),
                page=self.page_number,
                presliced_list=True,
                item_count=self.num_results,
                items_per_page=self.limit,
                url=_url
            )
        return self._page

    def _query(self, **kwargs):
        kwargs.update({'wt': 'json'})
        data = solr.get_connection().raw_query(**kwargs)
        return json.loads(data)

    def query(self, **kwargs):
        kw = dict(q=self.q, fq=self.fq,
                  start=self.start,
                  rows=self.limit,
                  fl='id, amount, score',
                  #stats='true',
                  #stats_field='amount',
                  sort='score desc, amount desc')

        if not kw['rows']:
            kw['rows'] = STREAM_BATCH_SIZE

        kw.update(self.solr_args)

        if len(self.facets):
            kw['facet'] = 'true'
            if not 'facet_limit' in kw:
                kw['facet_limit'] = 250
            kw['facet_mincount'] = 1
            kw['facet_sort'] = 'count'
            kw['facet_field'] = self.facets

        kw.update(kwargs)

        if kw['q'] is None or not len(kw['q']):
            kw['q'] = '*:*'

        return self._query(**kw)

    def state_url(self, add=None, remove=None):
        url = self.url or ''
        url = url.split('?', 1)[0]
        query = self.args.copy()
        if remove is not None:
            query = [kv for kv in query.items() if kv != remove]
        else:
            query = query.items()
        if add is not None:
            query.append(add)
        return url + '?' + urlencode([(k, v.encode('utf-8') if \
                    isinstance(v, unicode) else v) for (k, v) in \
                    query])

    @property
    def entries(self):
        # IDs in order requested
        ids = map(lambda x: x['id'], self.items)
        # Make a mapping between id and original index
        ids_map = dict((id_, idx) for idx, id_ in enumerate(ids))

        # Get entries. There must be a record in the database for
        # every id that comes back from Solr, otherwise this method
        # will start yielding None values.
        if len(ids):
            query = self.dataset.alias.c.id.in_(ids)
            entries = self.dataset.entries(query)
        else:
            entries = []
        entries_ordered = [None] * STREAM_BATCH_SIZE

        for entry in entries:
            entries_ordered[ids_map[entry['id']]] = entry
        for entry in entries_ordered:
            if entry is not None:
                yield entry

    @property
    def all_entries(self):
        for page in count(1):
            self._results = None
            self.page_number = page
            self.limit = STREAM_BATCH_SIZE
            for entry in self.entries:
                yield entry
            if (self.page_number * self.limit) > self.num_results:
                break

    def to_jsonp(self):
        facets = dict([(k, self.facet_values(k)) for k in self.facets])
        return write_browser_json(self.entries, self.stats, facets, response)

    def to_csv(self):
        return write_csv(self.all_entries, response)
