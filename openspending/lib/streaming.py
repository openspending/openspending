import json

from openspending.lib import solr_util as solr
from openspending.lib.browser import Browser
from openspending.lib.csvexport import generate_csv_row
from openspending.lib.jsonexport import generate_jsonp, to_json
from openspending.ui.lib.hypermedia import (entry_apply_links, dataset_apply_links)


class StreamingResponse(object):
    def __init__(self, datasets, params, pagesize=100):
        self.datasets = datasets
        self.params = params
        self.pagesize = pagesize

    def get_browser(self, page):
        current = dict(self.params)
        current['pagesize'] = self.pagesize
        current['page'] = page
        return Browser(**current)

    def make_entries(self, entries):
        for dataset, entry in entries:
            entry = entry_apply_links(dataset.name, entry)
            entry['dataset'] = dataset_apply_links(dataset.as_dict())
            yield entry

    def entries_iterator(self, initial_page=1):
        i = initial_page - 1
        while True:
            i += 1
            b = self.get_browser(i)
            try:
                b.execute()
            except solr.SolrException, e:
                yield json.dumps({'errors': [unicode(e)]})
                raise StopIteration

            count = 0
            for entry in self.make_entries(b.get_entries()):
                count += 1
                yield entry

            if count < self.pagesize:
                raise StopIteration


class CSVStreamingResponse(StreamingResponse):
    def response(self):
        header = True
        for entry in self.entries_iterator():
            yield generate_csv_row(entry, header)
            header = False


class JSONStreamingResponse(StreamingResponse):
    def __init__(self, *args, **kwargs):
        self.expand_facets = kwargs.pop('expand_facets', None)
        self.callback = kwargs.pop('callback', None)
        super(JSONStreamingResponse, self).__init__(*args, **kwargs)

    def response(self):
        b = self.get_browser(1)
        try:
            b.execute()
        except solr.SolrException, e:
            yield json.dumps({'errors': [unicode(e)]})
            raise StopIteration

        facets = b.get_facets()
        stats = b.get_stats()
        stats['results_count'] = stats['results_count_query']

        if self.expand_facets and len(self.datasets) == 1:
            self.expand_facets(facets, self.datasets[0])

        template = generate_jsonp({
            'stats': stats,
            'facets': facets,
            'results': [None]
        }, indent=0, callback=self.callback)
        parts = template.split('null')
        yield parts[0]

        # yield first batch
        first = True
        count = 0
        for entry in self.make_entries(b.get_entries()):
            count += 1
            if first:
                json_dict = to_json(entry)
            else:
                json_dict = ',' + to_json(entry)
            yield json_dict
            first = False

        if count < self.pagesize:
            raise StopIteration

        # yield rest
        for entry in self.entries_iterator(initial_page=2):
            json_dict = ',' + to_json(entry)
            yield json_dict
            first = False
        yield parts[1]
