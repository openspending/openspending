from openspending.core import cache
from openspending.lib.util import cache_hash
from openspending.inflation.aggregation import aggregate
from openspending.lib.indices import dataset_index, language_index, \
    territory_index, category_index


def memo_hash(f, *a, **kw):
    return cache_hash(*a, **kw)


@cache.memoize()
def cached_index(languages=[], territories=[], category=None):
    """ A proxy function to run cached calls against the dataset
    index (dataset index page and dataset.json). """
    datasets = dataset_index(languages, territories, category)
    return {
        'datasets': map(lambda d: d.as_dict(), datasets),
        'languages': language_index(datasets),
        'territories': territory_index(datasets),
        'categories': category_index(datasets)
    }

cached_index.make_cache_key = memo_hash


def clear_index_cache():
    cache.delete_memoized(cached_index)


@cache.memoize()
def cached_aggregate(dataset, measures=['amount'], drilldowns=None, cuts=None,
                     page=1, pagesize=10000, order=None, inflate=None):
    """ A proxy object to run cached calls against the dataset
    aggregation function. This is neither a concern of the data
    model itself, nor should it be repeated at each location
    where caching of aggregates should occur - thus it ends up
    here.
    For call docs, see ``model.Dataset.aggregate``. """
    return aggregate(dataset, measures=measures,
                     drilldowns=drilldowns, cuts=cuts,
                     page=page, pagesize=pagesize,
                     order=order, inflate=inflate)

cached_aggregate.make_cache_key = memo_hash
