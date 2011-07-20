from openspending.lib.util import check_rest_suffix
from openspending.model import Classifier


def create_classifier(name, taxonomy, label=u'', description=u'',
                      **classifier):
    '''create a :class:openspending.model.`classifier`. The ``name`` has to
    be unique for the ``taxonomy``. The ``classifier`` will be updated
    with the values for ``label``, ``description`` and
    ``**classifier``

    Arguments:

    ``name``
      name of the classifier. (``unicode``)
    ``taxonomy``
      The taxonomy to which the classifier ``name`` belongs.
      (``unicode``)
    ``label``, ``descripiton``, ``**classifiers``
      used to update the classifier for the first time

    Returns: An :class:`openspending.model.Classifier` object

    Raises:
       AssertionError if more than one ``Classifer`` object with the
       Name existes in the ``taxonomy``
    '''
    check_rest_suffix(name)
    query = {'name': name, 'taxonomy': taxonomy}
    assert Classifier.find(query).count() <= 1, \
        "Ambiguous classifier name (%s) in (%s)" % (name, taxonomy)
    if label:
        classifier['label'] = label
    if description:
        classifier['descripiton'] = description
    Classifier.c.update(query, {"$set": classifier}, upsert=True)
    return Classifier.find_one(query)


def get_classifier(name, taxonomy):
    '''Get the classifier object with the name ``name`` for the taxonomy
    ``taxonomy``.

    ``name``
      name of the classifier. (``unicode``)
    ``taxonomy``
      The taxonomy to which the classifier ``name`` belongs.
      (``unicode``)

    Returns: An :class:`openspending.model.Classifier` object if found or
    ``None``.
    '''
    query = {'name': name, 'taxonomy': taxonomy}
    return Classifier.find_one(query)
