from openspending.ui.test import TestCase
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

    def test_03_format_number(self):
        testsets = [
            [200, '200'],
            [2000, '2.0k'],
            [200000, '200.0k'],
            [2109400, '2.11m'],
            [-2103400, '-2.1m'],
            [2109400000, '2.11b'],
        ]
        self._check(helpers.format_number, testsets)

