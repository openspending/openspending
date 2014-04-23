from openspending.tests.base import ControllerTestCase

from pylons import url


class TestHomeController(ControllerTestCase):

    def test_index(self):
        response = self.app.get(url(controller='home', action='index'))
        assert 'OpenSpending' in response

    def test_locale(self):
        self.app.post(url(controller='home', action='set_locale'))
