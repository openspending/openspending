from colander import Invalid 

from ... import TestCase, helpers as h

from openspending.validation.model.views import views_schema
from openspending.validation.model.common import ValidationState

class TestViews(TestCase):

    def setup(self):
        self.model = h.model_fixture('default')
        self.state = ValidationState(self.model)

    def test_basic_validate(self):
        try:
            in_ = self.model['views']
            schema = views_schema(self.state)
            out = schema.deserialize(in_)
            assert len(out)==len(in_), out
        except Invalid, i:
            assert False, i.asdict()
    
    @h.raises(Invalid)
    def test_no_name(self):
        vs = list(self.model['views'])
        del vs[0]['name']
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_invalid_name(self):
        vs = list(self.model['views'])
        vs[0]['name'] = 'ba nana'
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_no_label(self):
        vs = list(self.model['views'])
        del vs[0]['label']
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_empty_label(self):
        vs = list(self.model['views'])
        vs[0]['label'] = ' '
        schema = views_schema(self.state)
        schema.deserialize(vs)

    @h.raises(Invalid)
    def test_invalid_cut(self):
        vs = list(self.model['views'])
        vs[0]['cuts'] = {'banana': 'split'}
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_invalid_dimension(self):
        vs = list(self.model['views'])
        vs[0]['dimension'] = 'banana'
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_invalid_dimension_attribute_name(self):
        vs = list(self.model['views'])
        vs[0]['dimension'] = 'function.name'
        schema = views_schema(self.state)
        schema.deserialize(vs)
    
    @h.raises(Invalid)
    def test_invalid_dimension_measure(self):
        vs = list(self.model['views'])
        vs[0]['dimension'] = 'amount'
        schema = views_schema(self.state)
        schema.deserialize(vs)


    @h.raises(Invalid)
    def test_invalid_drilldown(self):
        vs = list(self.model['views'])
        vs[0]['drilldown'] = 'banana'
        schema = views_schema(self.state)
        schema.deserialize(vs)

    def test_no_drilldown(self):
        vs = list(self.model['views'])
        vs[0]['drilldown'] = ''
        schema = views_schema(self.state)
        schema.deserialize(vs)
