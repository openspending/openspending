from openspending import mongo

def _aggregation_query_spec(dataset, include_spec):
    '''\
    Build a query spec from the include_spec and the dataset.
    Converts strings to int and float if possible.
    '''
    query_spec = include_spec
    query_spec['dataset._id'] = dataset['_id']
    for key, value in query_spec.items():
        # Todo: this needs to go into REST controller!
        if isinstance(value, basestring):
            try:
                value = int(value)
            except:
                pass
            try:
                value = float(value)
            except:
                pass
    return query_spec

def _aggregation_query(dataset, include_spec, fields=None):
    '''\
    Query helper for aggregations. Query mongodb for all entries
    where the dataset is *dataset* and the entry match the
    *include_spec*. The values in *query_spec* are converted
    to *int* or *float* if possible.

    It will return a cursor that emits entry ``dict`` objects. The information
    contained in the *dict*s can be limited by passing
    a list of *fields*.

    ``dataset``
        A dict-like ``dataset`` object
    ``include_spec``
        A dict with a (partial) mongodb query spec.
    ``fields``
        Optional. A list of field names to query.

    Returns: A :class:`pymongo.cursor.Cursor` object that emits
    dicts.
    '''
    from openspending import model

    # prepare query spec
    query_spec = _aggregation_query_spec(dataset, include_spec)

    # prepare fields
    if fields is not None:
        fields = set(fields + ['amount'])

    return model.entry.find(spec=query_spec, fields=fields)


def update_distincts(dataset_name):
    db = mongo.db
    db.system_js.compute_distincts(dataset_name)
