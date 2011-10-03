import logging

from pylons import request, tmpl_context as c
from pylons.controllers.util import abort
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.lib.cubes import find_cube
from openspending import model
from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.page import Page

log = logging.getLogger(__name__)

ENTRY_FIELDS = ["time", "amount", "currency", "_id"]
PAGE_SIZE = 100

class DimensionController(BaseController):

    @beaker_cache(invalidate_on_startup=True,
           cache_response=False,
           query_args=True)
    def index(self, dataset, format='html'):
        c.dataset = model.dataset.find_one_by('name', dataset)
        if not c.dataset:
            abort(404, _('Sorry, there is no dataset named %s') % dataset)
        c.dimensions = model.dimension.get_dataset_dimensions(c.dataset['name'])
        c.dimensions = [d for d in c.dimensions if d['key'] not in ENTRY_FIELDS]
        if format == 'json':
            return to_jsonp(list(c.dimensions))
        else:
            return render('dimension/index.html')

    @beaker_cache(invalidate_on_startup=True,
           cache_response=False,
           query_args=True)
    def view(self, dataset, dimension, format='html'):
        c.dataset = model.dataset.find_one_by('name', dataset)
        if not c.dataset:
            abort(404, _('Sorry, there is no dataset named %s') % dataset)
        if dimension in ENTRY_FIELDS or "." in dimension:
            abort(400, _('This is not a dimension'))
        c.meta = model.dimension.find_one({"dataset": c.dataset['name'],
                                           "key": dimension})
        if c.meta is None:
            c.meta = {}

        # TODO: pagination!
        try:
            page = int(request.params.get('page'))
        except:
            page = 1
        cube = find_cube(c.dataset, [dimension])
       # ok
        if cube is not None:
            try:
                result = cube.query([dimension], page=page, pagesize=PAGE_SIZE,
                                order=[('amount', True)])
            except Exception as e:
                error = str(e)
                if "too much data for sort" in error:
                    error = """Database tuning required: the dataset specified
                               is so large that it cannot be searched quickly
                               enough to fulfil your request in reasonable time.
                               Please request that an administrator add an
                               index to speed up this query."""
                abort(403, error)
            items = result.get('drilldown', [])
            c.values = [(d.get(dimension), d.get('amount')) for d in items]
        else:
            abort(403, "none")
            items = distinct(dimension, dataset_name=c.dataset['name'])
            c.values = [(i, 0.0) for i in items]

        if format == 'json':
            return to_jsonp({
                "values": c.values,
                "meta": c.meta})

        c.page = Page(c.values, page=page,
                      items_per_page=PAGE_SIZE)
        return render('dimension/view.html')
