
from flask import url_for

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture


class TestSlicerController(ControllerTestCase):

    def setUp(self):
        super(TestSlicerController, self).setUp()
        self.dataset = load_fixture('cra')
        self.user = make_account('test')

    def test_index(self):
        response = self.client.get(url_for('slicer.show_index'))
        assert 'Cubes OLAP' in response.data

    def test_cubes(self):
        response = self.client.get(url_for('slicer.list_cubes'))
        assert 'cra' in response.data

    def test_cube_model(self):
        response = self.client.get(url_for('slicer.cube_model',
                                           cube_name='cra'))
        assert 'cra' in response.data
        assert self.dataset.label in response.data, response.data
