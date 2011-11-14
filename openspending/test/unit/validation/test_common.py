from ... import TestCase, helpers as h
from openspending.validation.model.common import ValidationState

class TestValidationState(TestCase):

    def setup(self):
        self.state = ValidationState(h.model_fixture('default'))

    def test_list_attributes(self):
        attributes = list(self.state.attributes)
        assert len(attributes)==11, attributes
        assert 'amount' in attributes, attributes
        assert 'function.label' in attributes, attributes
        assert not 'foo' in attributes, attributes

    def test_list_dimensions(self):
        dimensions = list(self.state.dimensions)
        assert len(dimensions)==4, dimensions
        assert 'amount' not in dimensions, dimensions
        assert 'function' in dimensions, dimensions
        assert not 'foo' in dimensions, dimensions


