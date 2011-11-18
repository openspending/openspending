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
        self.cache_enabled = asbool(opt)
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

        key_parts = {'m': measure,
                     'd': sorted(drilldowns or []),
                     'c': sorted(cuts or []),
                     'o': order}
        key = hashlib.sha1(repr(key_parts)).hexdigest()

        if self.cache.has_key(key):
            log.debug("Cache hit: %s", key)
            result = self.cache.get(key)
        else:
            log.debug("Generating: %s", key)
            # Note that we're not passing pagination options. Since
            # the computational effort of giving a page is the same
            # as returning all, we're taking the network hit and 
            # storing the full result set in all cases.
            result = self.dataset.aggregate(measure=measure,
                                            drilldowns=drilldowns,
                                            cuts=cuts,
                                            page=1,
                                            pagesize=maxint,
                                            order=order)
            self.cache.put(key, result)

        # Restore pagination by splicing the cached result.
        offset = ((page-1)*pagesize)
        drilldown = result['drilldown']
        result['summary']['cached'] = True
        result['summary']['cache_key'] = key
        result['summary']['num_drilldowns'] = len(drilldown)
        result['summary']['page'] = page
        result['summary']['pages'] = int(math.ceil(len(drilldown)/float(pagesize)))
        result['summary']['pagesize'] = pagesize
        result['drilldown'] = drilldown[offset:offset+pagesize]
        return result

    def invalidate(self):
        """ Clear the cache. """
        self.cache.clear()



