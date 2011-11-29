import logging

from pylons import request, tmpl_context as c, response
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDimensionController

from openspending import model
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.page import Page
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.helpers import url_for
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.cache import AggregationCache
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp

log = logging.getLogger(__name__)

PAGE_SIZE = 100

class DimensionController(BaseController):

    extensions = PluginImplementations(IDimensionController)


    def _get_member(self, dataset, dimension_name, name):
        self._get_dataset(dataset)
        c.dimension = dimension_name
        for dimension in c.dataset.compounds:
            if dimension.name == dimension_name:
                cond = dimension.alias.c.name==name
                members = list(dimension.members(cond, limit=1))
                if not len(members):
                    abort(404, _('Sorry, there is no member named %r')
                            % name)
                c.member = members.pop()
                c.num_entries = dimension.num_entries(cond)
                return
        abort(404, _('Sorry, there is no dimension named %r') % dimension_name)


    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        if format == 'json':
            return to_jsonp([d.as_dict() for d in c.dataset.dimensions])
        else:
            return render('dimension/index.html')


    def view(self, dataset, dimension, format='html'):
        self._get_dataset(dataset)
        try:
            c.dimension = c.dataset[dimension]
        except KeyError:
            abort(404, _('This is not a dimension'))
        if not isinstance(c.dimension, model.Dimension):
            abort(404, _('This is not a dimension'))

        page = self._get_page('page')
        cache = AggregationCache(c.dataset)
        result = cache.aggregate(drilldowns=[dimension], page=page, 
                                 pagesize=PAGE_SIZE)
        items = result.get('drilldown', [])
        c.values = [(d.get(dimension), d.get('amount')) for d in items]

        if format == 'json':
            return to_jsonp({
                "values": c.values,
                "meta": c.dimension.as_dict()})

        c.page = Page(c.values, page=page,
                      item_count=result['summary']['num_drilldowns'],
                      items_per_page=PAGE_SIZE,
                      presliced_list=True)
        return render('dimension/view.html')


    def member(self, dataset, dimension, name, format="html"):
        self._get_member(dataset, dimension, name)

        handle_request(request, c, c.member, c.dimension)
        if c.view is None:
            self._make_browser()

        for item in self.extensions:
            item.read(c, request, response, c.member)

        if format == 'json':
            return to_jsonp(c.member)
        elif format == 'csv':
            return write_csv([c.member], response)
        else:
            return render('dimension/member.html')


    def entries(self, dataset, dimension, name, format='html'):
        self._get_member(dataset, dimension, name)

        handle_request(request, c, c.member, c.dimension)

        self._make_browser()
        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            return c.browser.to_csv()
        else:
            return render('dimension/entries.html')


    def _make_browser(self):
        url = url_for(controller='dimension', action='entries',
                dataset=c.dataset.name,
                dimension=c.dimension,
                name=c.member['name'])
        c.browser = Browser(c.dataset, request.params, url=url)
        c.browser.filter_by("+%s:\"%s\"" % (c.dimension, c.member['name']))
        c.browser.facet_by_dimensions()

