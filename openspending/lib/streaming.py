import json
import math

from openspending.lib import solr_util as solr
from openspending.lib.browser import Browser
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_browser_json
from openspending.lib.hypermedia import entry_apply_links, dataset_apply_links


class StreamingResponse(object):

    def __init__(self, datasets, params, pagesize=100):
        self.datasets = datasets
        self.params = params
        param_page = params['page']
        param_pagesize = params['pagesize']
        self.start_page = (param_page - 1) * param_pagesize / float(pagesize)
        self.start_page = int(math.floor(self.start_page)) + 1
        self.start_offset = int(((param_page - 1) * param_pagesize) % pagesize)
        self.pagesize = pagesize

    def get_browser(self, page):
        current = dict(self.params)
        current['pagesize'] = self.pagesize
        current['page'] = page
        self.browser = Browser(**current)
        return self.browser

    def make_entries(self, entries):
        for dataset, entry in entries:
            entry = entry_apply_links(dataset.name, entry)
            entry['dataset'] = dataset_apply_links(dataset.as_dict())
            yield entry

    def entries_iterator(self, initial_page=None):
        if initial_page is None:
            initial_page = self.start_page
        i = initial_page - 1
        total_count = 0
        while True:
            i += 1
            b = self.get_browser(i)
            try:
                b.execute()
            except solr.SolrException as e:
                yield json.dumps({'errors': [unicode(e)]})
                raise StopIteration

            count = 0
            for entry in self.make_entries(b.get_entries()):
                count += 1
                if total_count == 0 and count <= self.start_offset:
                    continue
                total_count += 1
                if total_count > self.params['pagesize']:
                    raise StopIteration
                yield entry

            if count < self.pagesize:
                # There are no more results for the next page
                raise StopIteration
            if total_count >= self.params['pagesize']:
                # We have enough results
                raise StopIteration


class CSVStreamingResponse(StreamingResponse):

    def response(self):
        return write_csv(self.entries_iterator())


class JSONStreamingResponse(StreamingResponse):

    def __init__(self, *args, **kwargs):
        self.expand_facets = kwargs.pop('expand_facets', None)
        self.callback = kwargs.pop('callback', None)
        super(JSONStreamingResponse, self).__init__(*args, **kwargs)

    def response(self):
        facets = self.browser.get_facets()
        stats = self.browser.get_stats()
        stats['results_count'] = self.params
        return write_browser_json(self.entries_iterator(), stats, facets)
