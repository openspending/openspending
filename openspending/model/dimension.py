from mongo import dictproperty
from changeset import Revisioned


class Dimension(Revisioned):

    id = dictproperty('_id')
    coll = dictproperty('collection')
    context = dictproperty('context')
    key = dictproperty('key')
    label = dictproperty('label')
