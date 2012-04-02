'''
This module implements views on the database.
'''
import logging
from collections import defaultdict
from datetime import datetime
from pylons import config

from openspending.model import Dataset
from openspending.ui.lib.cache import AggregationCache
from openspending.lib.jsonexport import to_json
from openspending.ui.lib import widgets

log = logging.getLogger(__name__)


def default_year(dataset):
    """ Guess a reasonable default year for this dataset or use
    the year specified on the dataset object. """
    current_year = str(datetime.utcnow().year)
    times = [m['time']['year'] for m in dataset['time'].members()]
    times = list(set(times))
    if dataset.default_time:
        return dataset.default_time
    if not len(times) or current_year in times:
        return current_year
    return max(times)


class View(object):

    def __init__(self, dataset, view):
        self.dataset = dataset
        self.config = view
        self.entity = view.get('entity').lower().strip()
        self.filters = view.get('filters', {})
        if self.entity == 'entity':
            self.filters['taxonomy'] = 'entity'
        self.name = view.get('name')
        self.label = view.get('label')
        self.dimension = view.get('dimension')
        self.drilldown = view.get('drilldown',
                                  view.get('breakdown'))
        self.cuts = view.get('cuts',
                             view.get('view_filters', {}))
        self.year = default_year(dataset)

    def match(self, obj, dimension=None):
        if isinstance(obj, Dataset):
            return self.entity == 'dataset'
        if self.dimension != dimension:
            return False
        for k, v in self.filters.items():
            if obj.get(k) != v:
                return False
        return True

    @classmethod
    def by_name(cls, dataset, obj, name, dimension=None):
        """get a``View`` with the name ``name`` from the object

        ``obj``
            a model object (instance of :class:`openspending.model.Base`)
        ``name``
            The name of the ``View``

        returns: An instance of :class:`View` if the view could
        be found.

        raises: ``ValueError`` if the view does not exist.
        """
        for data in dataset.data.get('views', []):
            view = cls(dataset, data)
            if view.name == name and view.match(obj, dimension):
                return view
        raise ValueError("View %s does not exist." % name)

    @classmethod
    def available(cls, dataset, obj, dimension=None):
        views = []
        for data in dataset.data.get('views', []):
            view = View(dataset, data)
            if view.match(obj, dimension):
                views.append(view)
        return views

    @property
    def vis_state(self):
        return {
            'drilldown': self.drilldown,
            'cuts': self.cuts,
            'year': self.year
            }

    @property
    def vis_widget(self):
        return widgets.get_widget('treemap')

    @property
    def table_state(self):
        return {
            'drilldowns': [self.drilldown],
            'cuts': self.cuts,
            'year': self.year
            }

    @property
    def table_widget(self):
        return widgets.get_widget('aggregate_table')


def handle_request(request, c, obj, dimension=None):
    view_name = request.params.get('_view', 'default')
    c.available_views = View.available(c.dataset, obj, dimension)
    try:
        c.view = View.by_name(c.dataset, obj, view_name,
                              dimension=dimension)
    except ValueError:
        c.view = None
        return
