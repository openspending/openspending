from itertools import izip_longest
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
PAGE_SIZE = 100 # Applies only to HTML output, not CSV or JSON

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
        # By default, we set limit to be the value of the limit query
        # param, unless no such query param is set.
        try:
            self.limit = int(self.args.get('limit'))
        except TypeError:
            self.limit = limit

        # If we subsequently call _set_limit with a smaller value
        # of the limit kwarg, then reduce or set the limit accordingly.
        if limit:
            self.limit = limit if not self.limit else min(limit, self.limit)

    def _set_page_number(self):
        try:
            self.page_number = int(self.args.get('page'))
        except TypeError:
            self.page_number = 1

    @property
    def start(self):
        if self.limit:
            return (self.page_number - 1) * self.limit
        else:
            return (self.page_number - 1) * STREAM_BATCH_SIZE

    @property
    def fq(self):
        filters = []
        filters.extend(self._filters)
        if self.dataset is not None:
            filters.append("+dataset:%s" % self.dataset.name)
        for field, value in self.filters:
            filters.append("+%s:\"%s\"" % (field, value))
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
        def _more():
            return self.results.get('response', {}).get('docs')

        res = _more()

        # If a limit is defined, just do the query and yield the results
        if self.limit:
            for item in res:
                yield item

        # Otherwise, we can assume that we're streaming, so do a query,
        # yield the results, then clear the results, go to the next page,
        # and repeat.
        else:
            while res:
                for item in res:
                    yield item
                self.page_number += 1
                self._results = None
                res = _more()

    @property
    def num_results(self):
        return self.results.get('response', {}).get('numFound')

    def facet_values(self, name):
        values = self.results.get('facet_counts', {}).get('facet_fields',
                {}).get(name, [])
        options = []
        for value in values[::2]:
            count = values[values.index(value)+1]
            options.append((value, count))
        return dict(options)

    @property
    def stats(self):
        return self.results.get('stats').get('stats_fields').get('amount')

    @property
    def page(self):
        if self._page is None:
            def _url(page, **kwargs):
                return self.state_url(('page', unicode(page)),
                                      ('page', unicode(self.page_number)))
            self._page = Page(
                self.results,
                page=self.page_number,
                item_count=self.num_results,
                items_per_page=self.limit,
                url=_url
            )

        return self._page

    def _query(self, **kwargs):
        kwargs.update({'wt': 'json'})
        response = solr.get_connection().raw_query(**kwargs)
        return json.loads(response)

    def query(self, **kwargs):
        kw = dict(q=self.q, fq=self.fq,
                  start=self.start,
                  rows=self.limit,
                  stats='true',
                  stats_field='amount',
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
        for batch in _batches(STREAM_BATCH_SIZE, self.items):
            # IDs in order requested
            ids = map(lambda x: x['id'], batch)
            # Make a mapping between id and original index
            ids_map = dict((id_, idx) for idx, id_ in enumerate(ids))

            # Get entries. There must be a record in the database for
            # every id that comes back from Solr, otherwise this method
            # will start yielding None values.
            query = self.dataset.alias.c.id.in_(ids)
            entries = self.dataset.entries(query)
            entries_ordered = [None] * len(entries)

            for entry in entries:
                entries_ordered[ids_map[entry['id']]] = entry

            for entry in entries_ordered:
                yield _entry_filter(entry)

    def to_jsonp(self):
        self._set_limit(None)
        facets = dict([(k, self.facet_values(k)) for k in self.facets])
        return write_browser_json(self.entries, self.stats, facets, response)

    def to_csv(self):
        self._set_limit(None)
        return write_csv(self.entries, response)

def _entry_filter(entry):
    def kill(entry, path):
        try:
            if len(path) == 1:
                del entry[path[0]]
            else:
                kill(entry[path[0]], path[1:])
        except KeyError:
            pass

    kill(entry, ['_csv_import_fp']) # provided by 'provenance' key
    kill(entry, ['dataset', 'entry_custom_html'])
    kill(entry, ['dataset', 'description'])

    for k in entry.iterkeys():
        if isinstance(entry[k], dict):
            kill(entry[k], ['ref'])

    return entry

def _batches(n, iterable):
    args = [iter(iterable)] * n
    none = object() # Create simple unique object
    for batch in izip_longest(fillvalue=none, *args):
        yield filter(lambda x: x is not none, batch)
