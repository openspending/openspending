from flask import url_for

from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import load_fixture


class TestRestController(ControllerTestCase):

    def setUp(self):
        super(TestRestController, self).setUp()
        load_fixture('cra')
        self.cra = Dataset.by_name('cra')

    def test_dataset(self):
        response = self.client.get(url_for('dataset.view',
                                    format='json',
                                    dataset=self.cra.name))

        assert '"name": "cra"' in response.data, response.data

    def test_entry(self):
        q = self.cra.model['from'].alias.c.name == 'Dept047'
        example = list(self.cra.model.entries(q, limit=1)).pop()

        response = self.client.get(url_for('entry.view',
                                    dataset=self.cra.name,
                                    format='json',
                                    id=str(example['id'])))

        assert '"id":' in response.data, response.data
        assert '"cofog1":' in response.data, response.data
        assert '"from":' in response.data, response.data
        assert '"Dept047"' in response.data, response.data


class TestEntryController(ControllerTestCase):

    def setUp(self):
        super(TestEntryController, self).setUp()
        load_fixture('cra')
        self.cra = Dataset.by_name('cra')

    def test_view(self):
        t = list(self.cra.model.entries(limit=1)).pop()
        response = self.client.get(url_for('entry.view', dataset='cra',
                                           id=t['id']))
        assert 'cra' in response.data

    def test_inflated_view(self):
        """
        Test whether a view of an entry can be inflated. This is done by
        adding a url parameter inflate containing the target year
        for inflation.

        This test has hard coded values based on existing inflation data used
        by an external module. This may therefore need updating should the
        inflation data become more accurate with better data.
        """

        # There is only a single entry with this amount so we can safely
        # pop it and know that it is for the year 2010 but we assert it
        # to be absolutely sure
        t = list(self.cra.model.entries('amount=-22400000')).pop()
        assert t['time']['year'] == '2010', \
            "Test entry isn't from the year 2010"

        # Get an inflated response
        response = self.client.get(url_for('entry.view',
                                           dataset='cra', id=t['id'],
                                           inflate='2011'))
        assert '200' in response.status, \
            "Inflated entry isn't successful (status code isn't 200)"

        # Check for inflation adjustments
        assert 'Adjusted for inflation' in response.data, \
            "Entry is not adjusted for inflation"
        assert '22,400,000' in response.data, \
            "Original amount not in inflated entry response"
        assert '23,404,469' in response.data, \
            "Inflated amount is not in inflated entry response"

        # Try a non-working inflation (bad year)
        response = self.client.get(url_for('entry.view',
                                           dataset='cra', id=t['id'],
                                           inflate='1000'))
        assert '200' in response.status, \
            "Inflated entry (bad year) unsuccessful (status code isn't 200)"
        assert 'Unable to adjust for inflation' in response.data, \
            "Inflation warning not present in inflated entry response (bad)"
