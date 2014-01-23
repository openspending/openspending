from .. import ControllerTestCase, url


class TestHomeController(ControllerTestCase):

    def test_index(self):
        response = self.app.get(url(controller='home', action='index'))
        assert 'OpenSpending' in response

    def test_locale(self):
        response = self.app.post(url(controller='home', action='set_locale'))
