from nose.tools import assert_raises

from openspending.test.unit.model.helpers import \
        SIMPLE_MODEL
from openspending.test import DatabaseTestCase, helpers as h

from openspending.model import meta as db
from openspending.model import Dataset


class TestAttributeDimension(DatabaseTestCase):
    def setup(self):
        super(TestAttributeDimension, self).setup()
        self.engine = db.engine
        self.meta = db.metadata
        self.meta.bind = self.engine
        self.ds = Dataset(SIMPLE_MODEL)
        self.field = self.ds['field']

    def test_is_compound(self):
        h.assert_false(self.field.is_compound)


class TestCompoundDimension(DatabaseTestCase):

    def setup(self):
        super(TestCompoundDimension, self).setup()
        self.engine = db.engine
        self.meta = db.metadata
        self.meta.bind = self.engine
        self.ds = h.load_fixture('cra')
        self.entity = self.ds['from']
        self.classifier = self.ds['cofog1']

    def test_is_compound(self):
        h.assert_true(self.entity.is_compound)

    def test_basic_properties(self):
        assert self.entity.name == 'from', self.entity.name
        assert self.classifier.name == 'cofog1', self.classifier.name

    def test_generated_tables(self):
        #assert not hasattr(self.entity, 'table'), self.entity
        #self.ds.generate()
        assert hasattr(self.entity, 'table'), self.entity
        assert self.entity.table.name == 'cra__' + self.entity.taxonomy, self.entity.table.name
        assert hasattr(self.entity, 'alias')
        assert self.entity.alias.name == self.entity.name, self.entity.alias.name
        cols = self.entity.table.c
        assert 'id' in cols
        assert_raises(KeyError, cols.__getitem__, 'field')

    def test_attributes_exist_on_object(self):
        assert len(self.entity.attributes) == 3, self.entity.attributes
        assert_raises(KeyError, self.entity.__getitem__, 'field')
        assert self.entity['name'].name == 'name'
        assert self.entity['name'].datatype == 'string'

    def test_attributes_exist_on_table(self):
        assert hasattr(self.entity, 'table'), self.entity
        assert 'name' in self.entity.table.c, self.entity.table.c
        assert 'label' in self.entity.table.c, self.entity.table.c

    def test_members(self):
        members = list(self.entity.members())
        h.assert_equal(len(members), 5)

        members = list(self.entity.members(self.entity.alias.c.name == 'Dept032'))
        h.assert_equal(len(members), 1)
