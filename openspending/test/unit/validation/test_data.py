from ... import TestCase, helpers as h
from openspending.validation.data import convert_types

class TestTypes(TestCase):

    def test_convert_types_value(self):
        mapping = {
                    "foo": {"column": "foo", 
                           "datatype": "string"}
                  }
        row = {"foo": "bar"}
        out = convert_types(mapping, row)
        assert isinstance(out, dict), out
        assert 'foo' in out, out
        assert out['foo']=='bar'

    def test_convert_types_compound(self):
        mapping = {
                    "foo": {"fields": [
                        {"name": "name", "column": "foo_name", 
                            "datatype": "string"},
                        {"name": "label", "column": "foo_label", 
                            "datatype": "string"}
                        ]
                    }
                  }
        row = {"foo_name": "bar", "foo_label": "qux"}
        out = convert_types(mapping, row)
        assert isinstance(out, dict), out
        assert 'foo' in out, out
        assert isinstance(out['foo'], dict), out
        assert out['foo']['name']=='bar'
        assert out['foo']['label']=='qux'

    def test_convert_types_casting(self):
        mapping = {
                    "foo": {"column": "foo", 
                           "datatype": "float"}
                  }
        row = {"foo": "5.0"}
        out = convert_types(mapping, row)
        assert isinstance(out, dict), out
        assert 'foo' in out, out
        assert out['foo']==5.0

