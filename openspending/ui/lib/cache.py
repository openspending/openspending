from sys import maxint
import math
import hashlib
import logging

from paste.deploy.converters import asbool
from pylons import cache, config, app_globals
from openspending.ui.lib.aggregation import aggregate
log = logging.getLogger(__name__)

class AggregationCache(object):
    """ A proxy object to run cached calls against the dataset 
    aggregation function. This is neither a concern of the data 
    model itself, nor should it be repeated at each location 
    where caching of aggregates should occur - thus it ends up 
    here. """

    def __init__(self, dataset, type='dbm'):
        self.dataset = dataset
        self.cache_enabled = app_globals.cache_enabled and \
                not self.dataset.private
        self.cache = cache.get_cache('DSCACHE_' + dataset.name,
                                     type=type)

    def aggregate(self, measures=['amount'], drilldowns=None, cuts=None,
        page=1, pagesize=10000, order=None, inflate=None):
        """ For call docs, see ``model.Dataset.aggregate``. """

        # Initialise cache key
        key = None
        # If caching is enabled we try to fetch this from the cache
        if self.cache_enabled:
            # Key parts of the request, used to compute the cache key
            key_parts = (self.dataset.updated_at.isoformat(),
                         sorted(measures),
                         sorted(drilldowns or []),
                         sorted(cuts or []),
                         order, page, pagesize, inflate)
            key = hashlib.sha1(repr(key_parts)).hexdigest()

            # If the cache key exists we serve directly from the cache
            if self.cache.has_key(key):
                log.debug("Cache hit: %s", key)
                return self.cache.get(key)
        else:
            # Debug message to show caching is disabled
            log.debug("Caching is disabled.")

        # If it didn't exist in the cache we perform the aggregation and
        # store it in the cache with the given cache key
        result = aggregate(self.dataset, measures=measures,
                           drilldowns=drilldowns, cuts=cuts,
                           page=page, pagesize=pagesize,
                           order=order, inflate=inflate)

        # If caching is enabled we add the result to the cache
        if self.cache_enabled:
            log.debug("Generating key: %s", key)
            result['summary']['cached'] = True
            result['summary']['cache_key'] = key
            self.cache.put(key, result)

        return result

    def invalidate(self):
        """ Clear the cache. """
        self.cache.clear()



