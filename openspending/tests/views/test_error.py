from openspending.tests.base import ControllerTestCase


class TestErrors(ControllerTestCase):

    def test_error_404(self):
        response = self.client.get('/akhkfhdjkhf/fgfdghfdh')
        assert 'OpenSpending' in response.data
        assert 'Not Found' in response.data

    def test_error_403(self):
        response = self.client.get('/dashboard')
        assert 'OpenSpending' in response.data
        assert 'Forbidden' in response.data
