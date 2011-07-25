from . import Dataset
from .mongo import dictproperty, relationalproperty
from .changeset import Revisioned

class Entry(Revisioned):

    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')

    amount = dictproperty('amount')
    currency = dictproperty('currency')

    flags = dictproperty('flags')
    dataset = relationalproperty('dataset', Dataset)