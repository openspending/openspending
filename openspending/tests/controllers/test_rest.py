from openspending.model.dataset import Dataset
from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import load_fixture

from pylons import url


class TestRestController(ControllerTestCase):

    def setup(self):
        super(TestRestController, self).setup()
        load_fixture('cra')
        self.cra = Dataset.by_name('cra')

    def test_dataset(self):
        response = self.app.get(url(controller='dataset',
                                    action='view',
                                    format='json',
                                    dataset=self.cra.name))

        assert '"name": "cra"' in response, response

    def test_entry(self):
        q = self.cra['from'].alias.c.name == 'Dept047'
        example = list(self.cra.entries(q, limit=1)).pop()

        response = self.app.get(url(controller='entry',
                                    action='view',
                                    dataset=self.cra.name,
                                    format='json',
                                    id=str(example['id'])))

        assert '"id":' in response, response
        assert '"cofog1":' in response, response
        assert '"from":' in response, response
        assert '"Dept047"' in response, response
