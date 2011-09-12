'''
This module implements views on the database.
'''
import logging
from collections import defaultdict

from pylons.decorators.cache import beaker_cache

from openspending import mongo
from openspending import model
from openspending.lib.cubes import Cube, find_cube

log = logging.getLogger(__name__)

class View(object):

    def __init__(self, dataset, name, label, dimension,
                 drilldown=None, cuts={}):
        self.dataset = dataset
        self.name = name
        self.label = label
        self.dimension = dimension
        self.drilldown = drilldown
        self.cuts = cuts

    def apply_to(self, obj, filter):
        """
        Applies the view to all entities in the same collection of
        ``obj`` that match the query ``filter``.

        ``obj``
            a model object (instance of :class:`openspending.model.Base`)
        ``filter``
            a :term:`mongodb query spec`
        """
        data = self.pack()
        mongo.db[obj.collection].update(
            filter,
            {'$set': {'views.%s' % self.name: data}},
            multi=True
        )

    @classmethod
    def by_name(cls, obj, name):
        """get a``View`` with the name ``name`` from the object

        ``obj``
            a model object (instance of :class:`openspending.model.Base`)
        ``name``
            The name of the ``View``

        returns: An instance of :class:`View` if the view could
        be found.

        raises: ``ValueError`` if the view does not exist.
        """
        if not 'views' in obj:
            raise ValueError("%s has no views." % obj)
        view_data = obj.get('views').get(name)
        if view_data is None:
            raise ValueError("View %s does not exist." % name)
        return cls.unpack(name, view_data)

    def pack(self):
        """
        Convert view to a form suitable for storage in MongoDB.
        Internal method, no API.
        """
        return {
            "label": self.label,
            "dataset": self.dataset.get('name'),
            "dimension": self.dimension,
            "drilldown": self.drilldown,
            "cuts": self.cuts
            }

    @classmethod
    def unpack(cls, name, data):
        """
        Create a  :class:`View` instance from a view ``name``
        and a datastructure ``data`` (like it is created by
        :meth:`pack`). Internal mehtod, no API.

        """
        dataset = model.dataset.find_one_by('name', data.get('dataset'))
        return cls(dataset, name, data.get('label'), data.get('dimension'),
                   drilldown=data.get('drilldown'),
                   cuts=data.get('cuts', {}))

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

    @property
    def signature(self):
        return "view_%s_%s" % (self.name, "_".join(sorted(self.full_dimensions)))

    def compute(self):
        # TODO: decide if this is a good idea
        if not find_cube(self.dataset, self.full_dimensions):
            Cube.define_cube(self.dataset, self.signature, self.full_dimensions)


class ViewState(object):

    def __init__(self, obj, view, time):
        self.obj = obj
        self.view = view
        self.time = time

        self._totals = None
        self._aggregates = None

    @property
    def available_views(self):
        return self.obj.get('views', {})

    @property
    def cuts(self):
        _filters = self.view.cuts.items()
        _filters.append((self.view.dimension + "._id", self.obj.get('_id')))
        return _filters

    @property
    def totals(self):
        if self._totals is None:
            self._totals = {}
            cube = find_cube(self.view.dataset, self.view.base_dimensions)
            if cube is None:
                log.warn("Run-time has view without cube: %s",
                        self.view.base_dimensions)
                return self._totals
            results = cube.query(['year'], self.cuts)
            for entry in results.get('drilldown'):
                self._totals[str(entry.get('year'))] = entry.get('amount')
        return self._totals

    @property
    def aggregates(self):
        if self._aggregates is None:
            if self.view.drilldown is None:
                return []
            res = defaultdict(dict)
            drilldowns = []
            cube = find_cube(self.view.dataset, self.view.full_dimensions)
            if cube is None:
                log.warn("Run-time has view without cube: %s",
                        self.view.full_dimensions)
                return []
            results = cube.query(['year', self.view.drilldown], self.cuts)
            for entry in results.get('drilldown'):
                d = entry.get(self.view.drilldown)
                if not d in drilldowns:
                    drilldowns.append(d)
                res[drilldowns.index(d)][str(entry.get('year'))] = \
                        entry.get('amount')
            self._aggregates = [(drilldowns[k], v) for k, v in res.items()]
            # sort aggregations by time
            if self.time is not None:
                self._aggregates = sorted(self._aggregates, reverse=True,
                    key=lambda (k, v): v.get(self.time, 0))
        return self._aggregates


@beaker_cache(invalidate_on_startup=True, cache_response=False)
def times(dataset, time_axis):
    return sorted(model.entry.find({'dataset.name': dataset}).distinct(time_axis))


def handle_request(request, c, obj):
    view_name = request.params.get('_view', 'default')
    try:
        c.view = View.by_name(obj, view_name)
    except ValueError:
        c.view = None
        return

    c.dataset = c.view.dataset
    if c.dataset is None:
        return
    time_axis = c.dataset.get('time_axis', 'time.from.year')
    req_time = request.params.get('_time')
    c.times = times(c.dataset.get('name'), time_axis)
    if req_time in c.times:
        c.state['time'] = req_time
    c.time = c.state.get('time')
    if c.time not in c.times and len(c.times):
        c.time = c.dataset.get('default_time', c.times[-1])
    # TODO: more clever way to set comparison time
    c.time_before = None
    if c.time and c.times.index(c.time) > 0:
        c.time_before = c.times[c.times.index(c.time) - 1]
    c.viewstate = ViewState(obj, c.view, c.time)
