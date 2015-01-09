from nose.tools import assert_raises

from openspending.tests.helpers import model_fixture, load_fixture
from openspending.tests.base import DatabaseTestCase

from openspending.core import db
from openspending.model.dataset import Dataset


class TestAttributeDimension(DatabaseTestCase):

    def setUp(self):
        super(TestAttributeDimension, self).setUp()
        self.engine = db.engine
        self.meta = db.metadata
        self.meta.bind = self.engine
        self.ds = Dataset(model_fixture('simple'))
        self.field = self.ds.model['field']

    def test_is_compound(self):
        assert not self.field.is_compound


class TestCompoundDimension(DatabaseTestCase):

    def setUp(self):
        super(TestCompoundDimension, self).setUp()
        self.engine = db.engine
        self.meta = db.metadata
        self.meta.bind = self.engine
        self.ds = load_fixture('cra')
        self.entity = self.ds.model['from']
        self.classifier = self.ds.model['cofog1']

    def test_is_compound(self):
        assert self.entity.is_compound

    def test_basic_properties(self):
        assert self.entity.name == 'from', self.entity.name
        assert self.classifier.name == 'cofog1', self.classifier.name

    def test_generated_tables(self):
        assert hasattr(self.entity, 'table'), self.entity
        assert self.entity.table.name == 'cra__' + \
            self.entity.taxonomy, self.entity.table.name
        assert hasattr(self.entity, 'alias')
        assert self.entity.alias.name == self.entity.name, \
            self.entity.alias.name
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
        assert len(members) == 5

        members = list(
            self.entity.members(
                self.entity.alias.c.name == 'Dept032'))
        assert len(members) == 1
