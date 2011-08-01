from ..lib.util import check_rest_suffix
from .. import mongo
from . import base

collection = 'classifier'

base.init_model_module(__name__, collection)

# classifier objects may have the following fields
#   _id
#   name
#   taxonomy
#   level
#   label
#   description
#   parent

required_filters = ("taxonomy", "name")

def create(doc):
    """\
    Create a classifier from document ``doc``.

    Document keys:

    ``name``
      Name of the classifier. Must be unique within the ``taxonomy``.
    ``taxonomy``
      The taxonomy to which the classifier belongs.
    ``label``, ``description``, etc.
      Other classifier keys.

    Returns: The created/update object _id

    Raises:
       AssertionError if more than one ``classifier`` object with the
       given ``name`` exists in the ``taxonomy``
    """
    check_rest_suffix(doc['name'])
    query = {'name': doc['name'], 'taxonomy': doc['taxonomy']}
    curs = base.find(collection, query)

    if curs.count() > 1:
        raise base.ModelError(
            "Ambiguous classifier name (%(name)s) in taxonomy '%(taxonomy)s'!"
            % doc
        )
    elif curs.count() == 1:
        _id = curs[0]['_id']
        base.update(collection, query, {"$set": doc})
        return base.get(collection, _id)
    else:
        return base.create(collection, doc)