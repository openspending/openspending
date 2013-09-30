from sys import maxint
import math
import hashlib
import logging

from paste.deploy.converters import asbool
from pylons import cache, config, app_globals

log = logging.getLogger(__name__)


class AggregationCache(object):
    """ A proxy object to run cached calls against the dataset 
    aggregation function. This is neither a concern of the data 
    model itself, nor should it be repeated at each location 
    where caching of aggreagtes should occur - thus it ends up 
    here. """

    def __init__(self, dataset, type='dbm'):
        self.dataset = dataset
        self.cache_enabled = app_globals.cache_enabled and \
                not self.dataset.private
        self.cache = cache.get_cache('DSCACHE_' + dataset.name,
                                     type=type)

    def aggregate(self, measures=['amount'], drilldowns=None, cuts=None,
        page=1, pagesize=10000, order=None):
        """ For call docs, see ``model.Dataset.aggregate``. """

        if not self.cache_enabled:
            # If caching is disabled we perform the aggregation and return it
            log.debug("Caching is disabled.")
            return self.dataset.aggregate(measures=measures,
                                          drilldowns=drilldowns,
                                          cuts=cuts, page=page,
                                          pagesize=pagesize,
                                          order=order)

        # Key parts of the aggregation request, used to compute the cache key
        key_parts = (self.dataset.updated_at.isoformat(),
                     sorted(measures),
                     sorted(drilldowns or []),
                     sorted(cuts or []),
                     order, page, pagesize)
        key = hashlib.sha1(repr(key_parts)).hexdigest()

        # If the cache key exists we serve directly from the cache
        if self.cache.has_key(key):
            log.debug("Cache hit: %s", key)
            result = self.cache.get(key)
        else:
            # If it didn't exist in the cache we perform the aggregation and
            # store it in the cache with the given cache key
            log.debug("Generating: %s", key)
            result = self.dataset.aggregate(measures=measures,
                                            drilldowns=drilldowns,
                                            cuts=cuts,
                                            page=page,
                                            pagesize=pagesize,
                                            order=order)
            self.cache.put(key, result)

        # Since we catch whether caching is enabled or not way up there we
        # can safely add caching values to the summary before returning it
        result['summary']['cached'] = True
        result['summary']['cache_key'] = key
        return result

    def invalidate(self):
        """ Clear the cache. """
        self.cache.clear()



