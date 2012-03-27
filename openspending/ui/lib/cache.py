from sys import maxint
import math
import hashlib
import logging

from paste.deploy.converters import asbool
from pylons import cache, config

log = logging.getLogger(__name__)


class AggregationCache(object):
    """ A proxy object to run cached calls against the dataset 
    aggregation function. This is neither a concern of the data 
    model itself, nor should it be repeated at each location 
    where caching of aggreagtes should occur - thus it ends up 
    here. """

    def __init__(self, dataset, type='dbm'):
        self.dataset = dataset
        opt = config.get('openspending.cache_enabled', 'True')
        self.cache_enabled = asbool(opt) and \
                not self.dataset.private
        self.cache = cache.get_cache('DSCACHE_' + dataset.name,
                                     type=type)

    def aggregate(self, measure='amount', drilldowns=None, cuts=None,
        page=1, pagesize=10000, order=None):
        """ For call docs, see ``model.Dataset.aggregate``. """

        if not self.cache_enabled:
            log.debug("Caching is disabled.")
            return self.dataset.aggregate(measure=measure,
                                          drilldowns=drilldowns,
                                          cuts=cuts, page=page,
                                          pagesize=pagesize,
                                          order=order)

        key_parts = (measure,
                     sorted(drilldowns or []),
                     sorted(cuts or []),
                     order, page, pagesize)
        key = hashlib.sha1(repr(key_parts)).hexdigest()

        if self.cache.has_key(key):
            log.debug("Cache hit: %s", key)
            result = self.cache.get(key)
        else:
            log.debug("Generating: %s", key)
            result = self.dataset.aggregate(measure=measure,
                                            drilldowns=drilldowns,
                                            cuts=cuts,
                                            page=page,
                                            pagesize=pagesize,
                                            order=order)
            self.cache.put(key, result)

        result['summary']['cached'] = True
        result['summary']['cache_key'] = key
        return result

    def invalidate(self):
        """ Clear the cache. """
        self.cache.clear()



