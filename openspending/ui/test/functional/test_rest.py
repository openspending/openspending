from openspending.model import Dataset, meta as db
from .. import ControllerTestCase, url, helpers as h

class TestRestController(ControllerTestCase):

    def setup(self):
        super(TestRestController, self).setup()
        h.load_fixture('cra')
        self.cra = Dataset.by_name('cra')

    def test_index(self):
        response = self.app.get(url(controller='rest', action='index'))
        for word in ['/cra', 'entries']:
            assert word in response, response

    def test_dataset(self):
        response = self.app.get(url(controller='dataset',
                                    action='view',
                                    format='json',
                                    name=self.cra.name))

        assert '"_id":' in response, response
        assert '"name": "cra"' in response, response

    def test_entry(self):
        q = self.cra['from'].alias.c.name=='Dept047'
        example = list(self.cra.materialize(q, limit=1)).pop()

        response = self.app.get(url(controller='entry',
                                    action='view',
                                    dataset=self.cra.name,
                                    format='json',
                                    id=str(example['id'])))

        assert '"_id":' in response, response
        assert '"cofog1":' in response, response
        assert '"from":' in response, response
        assert '"Dept047"' in response, response
