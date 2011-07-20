'''Code to query, create and edit Entry data
'''
from logging import getLogger

from openspending.lib.aggregator import update_distincts
from openspending.ui.lib.browser import Browser
from openspending.model import Dataset, Entry, mongo

log = getLogger(__name__)


def facets_for_fields(facet_fields, dataset_name=None, **query):
    '''Get the facets for the fields *facet_fields* for all elements
    that are part of the dataset *dataset_name* and that
    match ***query*.

    ``facet_fields``
         A ``list`` of field names
    ``dataset``
        A dataset name or a :class:`openspending.model.Dataset` object
    ``**query``
        Parameters for an *AND* query. Only the *key* values objects
        matching these queries will be counted.

    Returns: A ``dict`` where the keys are the names in the
    facet_fields list and the values are dictionaries with
    "<facet value>:<count>" items.
    '''
    # browser with no limit for facets.
    browser = Browser({'facet_limit': -1})
    browser.facet_by(*facet_fields)

    # we don't want any docs. Facets listed in the Response
    browser.limit(0)
    if dataset_name is not None:
        browser.filter_by('+dataset:%s' % dataset_name)

    for (key, value) in query.items():
        if isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        filter_ = '+%s:%s' % (key, value)
        browser.filter_by(filter_)

    return dict([(f, browser.facet_values(f)) for f in facet_fields])


def distinct(key, dataset_name=None, **query):
    '''Return the distinct values for `key` for all *Entry* objects
    matching the dataset_name or ***query*. It will query solr for
    a result. There may be short time frames where the result from
    solr does not match the distincts for a key in the datastore (mongodb).

    ``key``
        The key of the field for which the distinct will be returned
    ``dataset``
        A dataset name or a :class:`openspending.model.Dataset` object
    ``**query``
        Parameters for an *AND* query. Only the *key* values objects
        matching these queries will be counted. If you want to query
        by dataset **don't** add the condition here, use *dataset_name*.

    Returns: A list of distinct values.
    '''

    direct_mongo_query = False

    # the same keys used in serverside_js/compute_distincts.js
    not_aggregated_keys = ['_id', 'name', 'amount', 'classifiers',
                           'entities', 'currency']

    if ((dataset_name is None) or (len(query) > 0) or
        (key in not_aggregated_keys)):
        direct_mongo_query = True
    else:
        dataset = Dataset.c.find_one({'name': dataset_name},
                                    as_class=dict)
        if not dataset:
            raise ValueError('Dataset "%s" does not exist' % dataset_name)

    if not direct_mongo_query:
        collection_name = 'distincts__%s' % dataset_name
        db = mongo.db()

        if collection_name not in db.collection_names():
            # We need to create the distincts collection first
            update_distincts(dataset_name)
        distincts_collection = db[collection_name]
        log.info('use distincts collection %s' % collection_name)
        return distincts_collection.find({'value.keys': key}).distinct('_id')

    if direct_mongo_query:
        if dataset_name is not None:
            query['dataset.name'] = dataset_name
        return Entry.c.find(query).distinct(key)


def used_keys(dataset_name):
    collection_name = 'distincts__%s' % dataset_name
    db = mongo.db()
    if collection_name not in db.collection_names():
        update_distincts(dataset_name)
    db[collection_name].distinct('value')


def distinct_count(key, dataset_name):
    assert ('.' not in key or key.startswith('time.'))
    collection_name = 'distincts__%s' % dataset_name
    db = mongo.db()
    if collection_name not in db.collection_names():
        update_distincts(dataset_name)
    db[collection_name].find({'values': key})


def count(dataset_name=None, **query):
    '''Count the number of element that are in the *dataset_name*
    and match the ***query*.

    ``dataset``
        A dataset name or a :class:`openspending.model.Dataset` object
    ``**query``
        Parameters for an *AND* query. Only the *key* values objects
        matching these queries will be counted.

    Returns: The count as an int.
    '''

    browser = Browser({})

    # we don't want any docs. Facets listed in the Response
    browser.limit(0)
    if dataset_name is not None:
        browser.filter_by('+dataset:%s' % dataset_name)

    for (key, value) in query.items():
        if isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        filter_ = '+%s:%s' % (key, value)
        browser.filter_by(filter_)

    return browser.num_results


def classify_entry(entry, classifier, name):
    '''Update the *entry* to be classified with *classifier*.
    *entry* is mutated, but not returned.

    ``entry``
        A ``dict`` like object, e.g. an instance of
        :class:`openspending.model.Base`.
    ``classifier``
        A :class:`wdmg.model.Classifier` object
    ``name``
        This is the key where the value of the classifier
        will be saved. This my be the same as classifier['name'].

    return:``None``
    '''
    if classifier is None:
        return
    entry[name] = classifier.to_ref_dict()
    entry['classifiers'] = list(set(entry.get('classifiers', []) +
                                    [classifier.id]))


def entitify_entry(entry, entity, name):
    '''Update the *entry* to use the *entity* for the
    dimension *name*.

    ``entry``
        A ``dict`` like object, e.g. an instance of
        :class:`openspending.model.Base`.
    ``entity``
        A :class:`wdmg.model.entity` object
    ``name``
        This is the key where the value of the entity
        will be saved. This my be the same as entity['name'].

    return:``None``
    '''
    if entity is None:
        return
    entry[name] = entity.to_ref_dict()
    entry['entities'] = list(set(entry.get('entities', []) +
                                 [entity.id]))
