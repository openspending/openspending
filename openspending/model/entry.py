from .base import Base, dictproperty

class Entry(Base):

    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')

    amount = dictproperty('amount')
    currency = dictproperty('currency')

    flags = dictproperty('flags')
    dataset = dictproperty('dataset')