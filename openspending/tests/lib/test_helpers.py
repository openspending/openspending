from openspending.tests.base import TestCase
from openspending.ui.lib import helpers


class TestFormatNumber(TestCase):

    def _check(self, ourmethod, testsets):
        for inp, res in testsets:
            out = ourmethod(inp)
            assert out == res, (out, res)

    def test_01_positive(self):
        testsets = [
            [200, '200'],
            [2000, '2,000'],
            [2000000, '2,000,000'],
        ]
        self._check(helpers.format_number_with_commas, testsets)

    def test_02_negative(self):
        testsets = [
            [-200, '-200'],
            [-2000, '-2,000'],
            [-2000000, '-2,000,000'],
        ]
        self._check(helpers.format_number_with_commas, testsets)
