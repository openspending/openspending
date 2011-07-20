from mongo import *
from changeset import Revisioned

class Entity(Revisioned):
    
    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')
    
    
