from .. import ControllerTestCase, url


class TestContentController(ControllerTestCase):

    def test_sample(self):
        response = self.app.get(url(controller='content', action='view'))
