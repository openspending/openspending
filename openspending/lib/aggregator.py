from openspending import mongo
from openspending import model

def _aggregation_query_spec(dataset, include_spec):
    '''\
    Build a query spec from the include_spec and the dataset.
    Converts strings to int and float if possible.
    '''
    query_spec = include_spec
    query_spec['dataset._id'] = dataset.id
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

def _aggregation_query(dataset, include_spec, fields=None, as_class=None):
    '''\
    Query helper for aggregations. Query mongodb for all entries
    where the dataset is *dataset* and the entry match the
    *include_spec*. The values in *query_spec* are converted
    to *int* or *float* if possible.

    It will return a cursor that emits ``dict`` (not
    :class:`openspending.model.Entry) objects. The information
    contained in the *dict*s can be limited by passing
    a list of *fields*.

    ``dataset``
        A :class:`openspending.model.Dataset` object
    ``include_spec``
        A dict with a (partial) mongodb query spec.
    ``fields``
        Optional. A list of field names to query.
    ``as_class``
        The class that should be used as the default class for
        result objects. if `None` (*default*) the document_class
        configured for the database connection will be used.

    Returns: A :class:`pymongo.cursor.Cursor` object that emits
    dicts.
    '''

    # prepare query spec
    query_spec = _aggregation_query_spec(dataset, include_spec)

    # prepare fields
    if fields is not None:
        fields = set(fields + ['amount'])

    if as_class is None:
        as_class = mongo.db.connection.document_class

    return model.Entry.c.find(spec=query_spec, fields=fields,
                              as_class=as_class)


def update_distincts(dataset_name):
    db = mongo.db
    db.system_js.compute_distincts(dataset_name)
