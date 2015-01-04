import math
from flask import current_app

from openspending.lib.util import nestify


def legacy_name(name):
    # We were young and needed the money
    if name == 'year':
        return 'time.year'
    return name


def escape(val):
    for char in '_-"\'':
        if char in val:
            return '"%s"' % val
    return val


def get_browser(dataset):
    """ Get a cubes browser for the given dataset. """
    # TODO: Don't require request context
    # TODO: Cache browsers?
    return current_app.cubes_workspace.browser(dataset.name)


def aggregate(dataset, measures=['amount'], drilldowns=[], cuts=[],
              page=1, pagesize=10000, order=[]):
    """ This emulates an OpenSpending-style aggregation endpoint using the
    cubes browser equivalent call. """
    browser = get_browser(dataset)
    aggregates = ['num_entries'] + measures
    
    if order is None or not len(order):
        order = [(m, True) for m in measures]
    order = [(legacy_name(f), 'desc' if d else 'asc') for f, d in order]
    cuts = '|'.join(['%s:%s' % (legacy_name(c[0]), escape(c[1])) for c in cuts])

    aggregate = browser.aggregate(cell=cuts,
                                  aggregates=aggregates,
                                  drilldown=map(legacy_name, drilldowns),
                                  page=page - 1,
                                  page_size=pagesize,
                                  order=order)

    # total_cell_count is ``None`` if there is no drilldowns, not 0.
    num_drilldowns = max(1, aggregate.total_cell_count)

    drilldowns = [nestify(r) for r in aggregate]
    if not len(drilldowns):
        drilldowns.append(aggregate.summary)
    
    summary = aggregate.summary.copy()
    summary.update({
        'pagesize': pagesize,
        'page': page,
        'currency': {m: dataset.currency for m in measures},
        'num_drilldowns': num_drilldowns,
        'pages': int(math.ceil(num_drilldowns / float(pagesize)))
    })
    return {
        'summary': summary,
        'drilldown': drilldowns
    }
