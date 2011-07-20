from openspending import model
from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestRestController(ControllerTestCase):

    def setup(self):
        super(TestRestController, self).setup()
        h.load_fixture('cra')
        self.cra = model.Dataset.find_one({'name': 'cra'})

    def test_index(self):
        response = self.app.get(url(controller='rest', action='index'))
        for word in ['dataset', 'entry']:
            assert word in response, response

    def test_dataset(self):
        response = self.app.get(url(controller='dataset',
                                    action='view',
                                    format='json',
                                    id=self.cra.name))

        assert '"_id":' in response, response
        assert '"name": "cra"' in response, response

    def test_entry(self):
        example = model.Entry.find_one({
            'dataset.name': self.cra.name,
            'from.name': 'Dept047'
        })

        response = self.app.get(url(controller='entry',
                                    action='view',
                                    format='json',
                                    id=str(example.id)))

        assert '"_id":' in response, response
        assert '"cofog1":' in response, response
        assert '"from":' in response, response
        assert '"Dept047"' in response, response
