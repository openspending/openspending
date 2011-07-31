from logging import getLogger

from .. import mongo
from ..lib.aggregator import update_distincts

from .dataset import Dataset
from . import base
from . import classifier as m_classifier

log = getLogger(__name__)

collection = 'entry'

base.init_model_module(__name__, collection)

# entry objects probably have the following fields
#   _id
#   name
#   label
#   amount
#   currency
#   flags

def create(doc, dataset):
    doc['dataset'] = dataset.to_ref_dict()
    return base.create(collection, doc)

def get_dataset(obj):
    return Dataset.find_one({'_id': obj['dataset']['_id']})

def to_query_dict(obj, sep='.'):
    """ Flatten down a dictionary with some smartness. """
    def _flatten(orig):
        flat = {}
        for k, v in orig.items():
            if isinstance(v, dict):
                for sk, sv in _flatten(v).items():
                    flat[k + sep + sk] = sv
            else:
                flat[k] = v
        return flat
    return _flatten(obj)

def to_index_dict(obj):
    query_form = to_query_dict(obj)
    index_form = {}
    for k, v in query_form.items():
        k = k.replace('$', '')
        if k.endswith('._id'):
            k = k.replace('._id', '.id')
        if k.endswith('.name'):
            ck = k.replace('.name', '')
            if not ck in query_form.keys():
                index_form[ck] = v
        index_form[k] = v
    return index_form

def distinct(key, dataset_name=None, **query):
    '''Return the distinct values for `key` for all *entry* objects
    matching the dataset_name or **``query``. It will query solr for
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

        if collection_name not in mongo.db.collection_names():
            # We need to create the distincts collection first
            update_distincts(dataset_name)
        distincts_collection = mongo.db[collection_name]
        log.info('use distincts collection %s' % collection_name)
        return distincts_collection.find({'value.keys': key}).distinct('_id')

    if direct_mongo_query:
        if dataset_name is not None:
            query['dataset.name'] = dataset_name
        return base.find(collection, query).distinct(key)


def classify_entry(entry, classifier, name):
    '''Update the *entry* to be classified with *classifier*.
    *entry* is mutated, but not returned.

    ``entry``
        An entry ``dict``
    ``classifier``
        A :class:`openspending.model.Classifier` object
    ``name``
        This is the key where the value of the classifier
        will be saved. This my be the same as classifier['name'].

    return:``None``
    '''
    entry[name] = m_classifier.get_ref_dict(classifier)
    if 'classifiers' not in entry:
        entry['classifiers'] = []
    if classifier['_id'] not in entry['classifiers']:
        entry['classifiers'].append(classifier['_id'])

def entitify_entry(entry, entity, name):
    '''Update the *entry* to use the *entity* for the
    dimension *name*.

    ``entry``
        An entry ``dict``
    ``entity``
        A :class:`openspending.model.Entity` object
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
