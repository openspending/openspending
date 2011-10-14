import logging

from pylons import request, tmpl_context as c
from pylons.controllers.util import abort
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending import model
from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.page import Page

log = logging.getLogger(__name__)

PAGE_SIZE = 100

class DimensionController(BaseController):

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        c.dimensions = c.dataset.dimensions
        if format == 'json':
            return to_jsonp([d.as_dict() for d in c.dimensions])
        else:
            return render('dimension/index.html')

    def view(self, dataset, dimension, format='html'):
        self._get_dataset(dataset)
        try:
            c.dimension = c.dataset[dimension]
        except KeyError:
            abort(400, _('This is not a dimension'))
        if not isinstance(c.dimension, model.Dimension):
            abort(400, _('This is not a dimension'))

        # TODO: pagination!
        try:
            page = int(request.params.get('page'))
        except:
            page = 1
        result = c.dataset.aggregate(drilldowns=[dimension], page=page, 
                    pagesize=PAGE_SIZE)
        items = result.get('drilldown', [])
        c.values = [(d.get(dimension), d.get('amount')) for d in items]

        if format == 'json':
            return to_jsonp({
                "values": c.values,
                "meta": c.dimension.as_dict()})

        c.page = Page(c.values, page=page,
                      items_per_page=PAGE_SIZE)
        return render('dimension/view.html')
