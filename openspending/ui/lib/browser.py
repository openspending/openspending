from urllib import urlencode

from openspending import model
from openspending.lib import json
from openspending.lib import solr_util as solr
from openspending.lib.csvexport import write_csv
from openspending.ui.lib import jsonp
from openspending.ui.lib.page import Page

FILTER_PREFIX = "filter-"
DIMENSION_LABEL = ".label_facet"

class Browser(object):

    def __init__(self, dataset, args, url=None):
        self.args = args
        self.url = url
        self.dataset = dataset
        self._rows = None
        self._results = None
        self._page = None
        self.facets = []
        self.solr_args = {}
        self._filters = []

    def limit(self, num):
        self._rows = num

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

    @property
    def rows(self):
        if self._rows is not None:
            return self._rows

        try:
            r = int(self.args.get('limit'))
        except TypeError:
            r = None

        if not r or r > 100:
            self._rows = 100
        else:
            self._rows = r

        return self._rows

    @property
    def page_number(self):
        try:
            return int(self.args.get('page'))
        except TypeError:
            return 1

    @property
    def start(self):
        return (self.page_number-1)*self.rows

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
                page=int(self.args.get('page', 1)),
                item_count=self.num_results,
                items_per_page=self.rows,
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
                  rows=self.rows,
                  stats='true',
                  stats_field='amount',
                  sort='score desc, amount desc')
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
    def entities(self):
        ids = map(lambda i: i['id'], self.items)
        query = self.dataset.alias.c.id.in_(ids)
        entries = self.dataset.materialize(query)
        return list(entries)

    def to_jsonp(self):
        return jsonp.to_jsonp({
            'results': self.entities,
            'stats': self.stats,
            'facets': dict([(k, self.facet_values(k)) for k in self.facets])
        })

    def to_csv(self):
        from pylons import response
        return write_csv(self.entities, response)
