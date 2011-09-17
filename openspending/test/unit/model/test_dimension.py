from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

def mock_dimension():
    return {
        'key': 'bar',
        'label': 'some_dimension',
        'type': 'classifier'
    }

class TestDimension(DatabaseTestCase):

    def test_dimension_create_raise_if_type_none(self):
        d = mock_dimension()

        del d['type']
        h.assert_raises(ValueError,
                        model.dimension.create,
                        dataset_name='foo',
                        **d)

    def test_dimension_raise_if_type_value(self):
        d = mock_dimension()

        d['type'] = 'value'
        h.assert_raises(ValueError,
                        model.dimension.create,
                        dataset_name='foo',
                        **d)