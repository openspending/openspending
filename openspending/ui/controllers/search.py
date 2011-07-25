import logging

from pylons import request, tmpl_context as c

from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import ISolrSearch
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.helpers import url_for
from openspending.ui.lib.browser import Browser


log = logging.getLogger(__name__)


class SearchController(BaseController):

    extensions = PluginImplementations(ISolrSearch)

    def index(self):
        url = url_for(controller='search', action='index')
        c.browser = Browser(request.params, url=url)
        c.browser.facet_by_dimensions()
        self._get_totals(c.browser)
        return render('search/index.html')

    def _get_totals(self, browser):
        browser._results = browser.query(stats_facet='time.from.parsed')
        if browser.stats is None:
            return
        facets = browser.stats.get('facets')
        results = []
        for timenorm, val in facets.get('time.from.parsed', {}).items():
            results.append([timenorm, val['sum']])
        c.amounts = sorted(results)
