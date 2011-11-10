

from sqlalchemy import Integer, UnicodeText, Float, Unicode
from nose.tools import assert_raises

from openspending.test.unit.model.helpers import SIMPLE_MODEL, load_dataset
from openspending.test import DatabaseTestCase, helpers as h

from openspending.model import meta as db
from openspending.model import Dataset, AttributeDimension, \
        CompoundDimension, Measure, DateDimension

class TestDataset(DatabaseTestCase):

    def setup(self):
        super(TestDataset, self).setup()        
        self.ds = Dataset(SIMPLE_MODEL)
    
    #def teardown(self):
    #    #db.metadata.drop_all(engine=db.engine)
    #    pass

    def test_load_model_properties(self):
        assert self.ds.name==SIMPLE_MODEL['dataset']['name'], self.ds.name
        assert self.ds.label==SIMPLE_MODEL['dataset']['label'], self.ds.label

    def test_load_model_dimensions(self):
        assert len(self.ds.dimensions)==4,self.ds.dimensions
        assert isinstance(self.ds['time'], DateDimension), self.ds['time']
        assert isinstance(self.ds['field'], AttributeDimension), self.ds['field']
        assert isinstance(self.ds['to'], CompoundDimension), self.ds['to']
        assert isinstance(self.ds['function'], CompoundDimension), \
            self.ds['function']
        assert len(self.ds.measures)==1,self.ds.measures
        assert isinstance(self.ds['amount'], Measure), self.ds['amount']

    def test_value_dimensions_as_attributes(self):
        dim = self.ds['field']
        assert isinstance(dim.column.type, UnicodeText), dim.column
        assert 'field'==dim.column.name, dim.column
        assert dim.name=='field', dim.name
        assert dim.source_column==SIMPLE_MODEL['mapping']['field']['column'], \
                dim.source_column
        assert dim.label==SIMPLE_MODEL['mapping']['field']['label'], \
                dim.label
        assert dim.constant==None, dim.constant
        assert dim.default_value==None, dim.default_value
        assert dim.constant==None, dim.constant
        assert dim.dataset==self.ds, dim.dataset
        assert dim.datatype=='string', dim.datatype
        assert not hasattr(dim, 'table')
        assert not hasattr(dim, 'alias')

    def test_generate_db_entry_table(self):
        assert self.ds.table.name=='test__entry', self.ds.table.name
        cols = self.ds.table.c
        assert 'id' in cols
        assert isinstance(cols['id'].type, Unicode)
        # TODO: 
        assert 'time_id' in cols
        assert isinstance(cols['time_id'].type, Integer)
        assert 'amount' in cols
        assert isinstance(cols['amount'].type, Float)
        assert 'field' in cols
        assert isinstance(cols['field'].type, UnicodeText)
        assert 'to_id' in cols
        assert isinstance(cols['to_id'].type, Integer)
        assert 'function_id' in cols
        assert isinstance(cols['function_id'].type, Integer)
        assert_raises(KeyError, cols.__getitem__, 'foo')


class TestDatasetLoad(DatabaseTestCase):

    def setup(self):
        super(TestDatasetLoad, self).setup()
        self.ds = Dataset(SIMPLE_MODEL)
        self.engine = db.engine
    
    def test_load_all(self):
        load_dataset(self.ds)
        resn = self.engine.execute(self.ds.table.select()).fetchall()
        assert len(resn)==6,resn
        row0 = resn[0]
        assert row0['amount']==200, row0.items()
        assert row0['field']=='foo', row0.items()
    
    def test_flush(self):
        load_dataset(self.ds)
        resn = self.engine.execute(self.ds.table.select()).fetchall()
        assert len(resn)==6,resn
        self.ds.flush()
        resn = self.engine.execute(self.ds.table.select()).fetchall()
        assert len(resn)==0,resn
    
    def test_drop(self):
        tn = self.engine.table_names()
        assert 'test__entry' in tn, tn
        assert 'test__to' in tn, tn
        assert 'test__function' in tn, tn
        self.ds.drop()
        tn = self.engine.table_names()
        assert 'test__entry' not in tn, tn
        assert 'test__to' not in tn, tn
        assert 'test__function' not in tn, tn

    def test_dataset_count(self):
        load_dataset(self.ds)
        assert len(self.ds)==6,len(self.ds)

    def test_aggregate_simple(self):
        load_dataset(self.ds)
        res = self.ds.aggregate()
        assert res['summary']['num_entries']==6, res
        assert res['summary']['amount']==2690.0, res

    def test_aggregate_basic_cut(self):
        load_dataset(self.ds)
        res = self.ds.aggregate(cuts=[('field', u'foo')])
        assert res['summary']['num_entries']==3, res
        assert res['summary']['amount']==1000, res

    def test_aggregate_or_cut(self):
        load_dataset(self.ds)
        res = self.ds.aggregate(cuts=[('field', u'foo'), 
                                      ('field', u'bar')])
        assert res['summary']['num_entries']==4, res
        assert res['summary']['amount']==1190, res

    def test_aggregate_dimensions_drilldown(self):
        load_dataset(self.ds)
        res = self.ds.aggregate(drilldowns=['function'])
        assert res['summary']['num_entries']==6, res
        assert res['summary']['amount']==2690, res
        assert len(res['drilldown'])==2, res['drilldown']

    def test_aggregate_two_dimensions_drilldown(self):
        load_dataset(self.ds)
        res = self.ds.aggregate(drilldowns=['function', 'field'])
        assert res['summary']['num_entries']==6, res
        assert res['summary']['amount']==2690, res
        assert len(res['drilldown'])==5, res['drilldown']

    def test_materialize_table(self):
        load_dataset(self.ds)
        itr = self.ds.entries()
        tbl = list(itr)
        assert len(tbl)==6, len(tbl)
        row = tbl[0]
        assert isinstance(row['field'], unicode), row
        assert isinstance(row['function'], dict), row
        assert isinstance(row['to'], dict), row
