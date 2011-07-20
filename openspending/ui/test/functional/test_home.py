from openspending.ui.test import ControllerTestCase, url

class TestHomeController(ControllerTestCase):

    def test_index(self):
        response = self.app.get(url(controller='home', action='index'))
        assert 'OpenSpending' in response
