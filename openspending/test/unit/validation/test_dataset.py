from colander import Invalid 

from ... import TestCase, helpers as h

from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.common import ValidationState

class TestDataset(TestCase):

    def setup(self):
        self.model = h.model_fixture('default')
        self.state = ValidationState(self.model)

    def test_basic_validate(self):
        try:
            ds = self.model['dataset']
            schema = dataset_schema(self.state)
            out = schema.deserialize(ds)
            assert out.keys()==ds.keys(), out
        except Invalid, i:
            assert False, i.asdict()
    
    @h.raises(Invalid)
    def test_underscore_validate(self):
        ds = self.model['dataset'].copy()
        ds['name'] = 'test__'
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    
    @h.raises(Invalid)
    def test_reserved_name_validate(self):
        ds = self.model['dataset'].copy()
        ds['name'] = 'entRY'
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    
    @h.raises(Invalid)
    def test_invalid_currency(self):
        ds = self.model['dataset'].copy()
        ds['currency'] = 'glass pearls'
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    
    @h.raises(Invalid)
    def test_no_label(self):
        ds = self.model['dataset'].copy()
        del ds['label']
        schema = dataset_schema(self.state)
        schema.deserialize(ds)

    @h.raises(Invalid)
    def test_empty_label(self):
        ds = self.model['dataset'].copy()
        ds['label'] = '  '
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    
    @h.raises(Invalid)
    def test_no_description(self):
        ds = self.model['dataset'].copy()
        del ds['description']
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    
    @h.raises(Invalid)
    def test_empty_description(self):
        ds = self.model['dataset'].copy()
        ds['description'] = '  '
        schema = dataset_schema(self.state)
        schema.deserialize(ds)
    

