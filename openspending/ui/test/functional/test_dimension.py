import csv
import json
from StringIO import StringIO

from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestDimensionController(ControllerTestCase):

    def setup(self):
        super(TestDimensionController, self).setup()
        h.load_fixture('cra')

    def test_index(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('Paid to' in response, "'Paid to' not in response!")
        h.assert_true('Programme Object Group' in response, "'Programme Object Group' not in response!")
        h.assert_true('Capital/Current' in response, "'Paid by' not in response!")

    def test_index_descriptions(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index'))
        h.assert_true('The entity that the money was paid from.' in response,
                      "'The entity that the money was paid from.' not in response!")
        h.assert_true('Capital (one-off investment) or Current (on-going running costs)' in response,
                      "'Capital (one-off investment) or Current (on-going running costs)' not in response!")

    def test_index_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 9)
        h.assert_equal(obj[0]['key'], 'from')
        h.assert_equal(obj[0]['label'], 'Paid by')

    def test_index_csv(self):
        h.skip("CSV dimension index not yet implemented!")

    def test_view(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('The entity that the money was paid from.' in response,
                      "'The entity that the money was paid from.' not in response!")
        h.assert_true('Department for Work and Pensions' in response,
                      "'Department for Work and Pensions' not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from',
                                    format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['meta']['dataset'], 'cra')
        h.assert_equal(obj['meta']['key'], 'from')
        h.assert_equal(len(obj['values']), 5)
        # FIXME: why are these doubly-nested lists?
        h.assert_equal(obj['values'][0][0]['label'], 'Department for Work and Pensions')

    def test_view_csv(self):
        h.skip("CSV dimension view not yet implemented!")