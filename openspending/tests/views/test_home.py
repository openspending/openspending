from flask import url_for

from openspending.tests.base import ControllerTestCase


class TestHomeController(ControllerTestCase):

    def test_index(self):
        response = self.client.get(url_for('home.index'))
        assert 'OpenSpending' in response.data

    def test_locale(self):
        self.client.post(url_for('home.set_locale'))
