from .base import Base, dictproperty

class Dimension(Base):

    id = dictproperty('_id')
    coll = dictproperty('collection')
    context = dictproperty('context')
    key = dictproperty('key')
    label = dictproperty('label')
