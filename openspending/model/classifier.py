from mongo import *
from changeset import Revisioned

class Classifier(Revisioned):
    
    @property
    def context(self): 
        return self.get('scheme')
    
    id = dictproperty('_id')
    name = dictproperty('name')
    taxonomy = dictproperty('taxonomy')
    level = dictproperty('level')
    label = dictproperty('label')
    description = dictproperty('notes')
    
    parent = dictproperty('parent')

    required_filters = ("taxonomy", "name")
