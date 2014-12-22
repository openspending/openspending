import hashlib
import logging

from flask import current_app

from openspending.core import cache
from openspending.inflation.aggregation import aggregate
from openspending.lib.indices import dataset_index, language_index, \
    territory_index, category_index

log = logging.getLogger(__name__)


class DatasetIndexCache(object):

    """
    A proxy object to run cached calls against the dataset
    index (dataset index page and dataset.json)
    """

    def __init__(self, type='dbm'):
        """
        Initialise a dataset index cache
        """
        self.cache_enabled = current_app.config.get('CACHE')
        
    def invalidate(self):
        """
        Clear the cache. This should be called whenever the index changes.
        """
        cache.clear()

    def index(self, languages=[], territories=[], category=None):
        """
        Get an index of all public datasets, preferably served via
        the cache. Returns a DatasetIndices tuple if cache is hit.
        """

        # If caching is enabled we try to fetch this from the cache
        if self.cache_enabled:
            # Key parts of the request, used to compute the cache key
            key_parts = (category, sorted(languages),
                         sorted(territories))

            # Return a hash of the key parts as the cache key
            key = hashlib.sha1(repr(key_parts)).hexdigest()

            # If the cache key exists we serve directly from the cache
            if cache.get(key):
                log.debug("Index cache hit: %s", key)
                return cache.get(key)
        else:
            # Debug message to show caching is disabled
            log.debug("Caching is disabled.")

        # Get all of the datasets
        log.debug(languages)
        datasets = dataset_index(languages, territories, category)

        # Count territories, languages, and categories
        territories = territory_index(datasets)
        languages = language_index(datasets)
        categories = category_index(datasets)

        # Create a results dictionary. We need to transform the datasets
        # into dict for the caching (since the datasets are returned as
        # classes with functions that cannot be cached).
        results = {'datasets': map(lambda d: d.as_dict(), datasets),
                   'languages': languages, 'territories': territories,
                   'categories': categories}

        # Cache the results if we have caching enabled and then return
        # the results
        if self.cache_enabled:
            cache.set(key, results)

        return results


class AggregationCache(object):

    """ A proxy object to run cached calls against the dataset
    aggregation function. This is neither a concern of the data
    model itself, nor should it be repeated at each location
    where caching of aggregates should occur - thus it ends up
    here. """

    def __init__(self, dataset, type='dbm'):
        self.dataset = dataset
        self.cache_enabled = current_app.config.get('CACHE') and \
            not self.dataset.private

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
            if cache.get(key):
                log.debug("Cache hit: %s", key)
                return cache.get(key)
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
            cache.set(key, result)

        return result

    def invalidate(self):
        """ Clear the cache. """
        cache.clear()
