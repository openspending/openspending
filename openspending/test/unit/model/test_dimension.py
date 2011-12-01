from StringIO import StringIO
import csv
import unittest

from nose.tools import assert_raises

from openspending.test.unit.model.helpers import \
        SIMPLE_MODEL, load_dataset
from openspending.test import DatabaseTestCase, helpers as h

from openspending.model import meta as db
from openspending.model import Dataset

class TestCompoundDimension(DatabaseTestCase):

    def setup(self):
        self.engine = db.engine 
        self.meta = db.metadata #MetaData()
        self.meta.bind = self.engine
        self.ds = Dataset(SIMPLE_MODEL)
        self.entity = self.ds['to']
        self.classifier = self.ds['function']

    def test_basic_properties(self):
        assert self.entity.name=='to', self.entity.name
        assert self.classifier.name=='function', self.classifier.name
        
    def test_generated_tables(self):
        #assert not hasattr(self.entity, 'table'), self.entity
        #self.ds.generate()
        assert hasattr(self.entity, 'table'), self.entity
        assert self.entity.table.name=='test__' + self.entity.taxonomy, self.entity.table.name
        assert hasattr(self.entity, 'alias')
        assert self.entity.alias.name==self.entity.name, self.entity.alias.name
        cols = self.entity.table.c
        assert 'id' in cols
        assert_raises(KeyError, cols.__getitem__, 'field')

    def test_attributes_exist_on_object(self):
        assert len(self.entity.attributes)==2, self.entity.attributes
        assert_raises(KeyError, self.entity.__getitem__, 'field')
        assert self.entity['name'].name=='name'
        assert self.entity['name'].datatype=='string'

    def test_attributes_exist_on_table(self):
        assert hasattr(self.entity, 'table'), self.entity
        assert 'name' in self.entity.table.c, self.entity.table.c
        assert 'label' in self.entity.table.c, self.entity.table.c

