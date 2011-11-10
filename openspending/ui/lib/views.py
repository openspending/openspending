'''
This module implements views on the database.
'''
import logging
from collections import defaultdict

from openspending.model import Dataset

log = logging.getLogger(__name__)

class View(object):

    def __init__(self, dataset, view):
        self.dataset = dataset
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

    def match(self, obj, dimension=None):
        if isinstance(obj, Dataset):
            return self.entity == 'dataset'
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

    @property
    def base_dimensions(self):
        dimensions = [self.dimension, 'year']
        dimensions.extend(self.cuts.keys())
        return dimensions

    @property
    def full_dimensions(self):
        dimensions = self.base_dimensions
        if self.drilldown:
            dimensions.append(self.drilldown)
        return dimensions


class ViewState(object):

    def __init__(self, obj, view, time):
        self.obj = obj
        self.view = view
        self.time = time

        self._totals = None
        self._aggregates = None

    @property
    def dataset(self):
        return self.view.dataset

    @property
    def available_views(self):
        views = []
        for data in self.dataset.data.get('views', []):
            view = View(self.dataset, data)
            if view.match(self.obj):
                views.append(view)
        return views

    @property
    def cuts(self):
        _filters = self.view.cuts.items()
        if isinstance(self.obj, dict):
            _filters.append((self.view.dimension, self.obj['name']))
        return _filters

    @property
    def totals(self):
        if self._totals is None:
            self._totals = {}
            results = self.dataset.aggregate(drilldowns=['year'], 
                                             cuts=self.cuts)
            for entry in results.get('drilldown'):
                self._totals[str(entry.get('year'))] = entry.get('amount')
        return self._totals

    @property
    def aggregates(self):
        if self._aggregates is None:
            if self.view.drilldown is None:
                return []
            res = defaultdict(dict)
            drilldowns = {}
            query = ['year', self.view.drilldown]
            results = self.dataset.aggregate(drilldowns=query,
                                             cuts=self.cuts)
            for entry in results.get('drilldown'):
                d = entry.get(self.view.drilldown)
                # Get a hashable key for the drilldown
                key = d['id'] if isinstance(d, dict) else d
                # Store a reference to this drilldown
                drilldowns[key] = d
                # Store drilldown value for this year
                res[key][str(entry.get('year'))] = entry.get('amount')
            self._aggregates = [(drilldowns[k], v) for k, v in res.items()]
            # sort aggregations by time
            if self.time is not None:
                self._aggregates = sorted(self._aggregates,
                                          reverse=True,
                                          key=lambda (k, v): v.get(self.time, 0))
        return self._aggregates



def _set_time_context(request, c):
    # TODO: this is an unholy mess that needs to be killed
    # with fire.
    req_time = request.params.get('_time')
    c.times = c.dataset.times()
    if req_time in c.times:
        c.state['time'] = req_time
    c.time = c.state.get('time')
    if c.time not in c.times and len(c.times):
        c.time = c.dataset.default_time or c.times[-1]
    # TODO: more clever way to set comparison time
    c.time_before = None
    if c.time and c.time in c.times:
        c.time_before = c.times[c.times.index(c.time) - 1]

def handle_request(request, c, obj, dimension=None):
    view_name = request.params.get('_view', 'default')
    try:
        c.view = View.by_name(c.dataset, obj, view_name,
                              dimension=dimension)
    except ValueError:
        c.view = None
        return

    _set_time_context(request, c)
    c.viewstate = ViewState(obj, c.view, c.time)
