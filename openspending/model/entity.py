from .base import Base, dictproperty

class Entity(Base):

    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')


