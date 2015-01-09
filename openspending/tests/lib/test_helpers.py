from openspending.tests.base import TestCase
from openspending.lib import helpers, filters


class TestFormatNumber(TestCase):

    def _check(self, ourmethod, testsets):
        for inp, res in testsets:
            out = ourmethod(inp, None, locale='en')
            assert out == res, (out, res)

    def test_01_positive(self):
        testsets = [
            [200, '$200.00'],
            [2000, '$2,000.00'],
            [2000000, '$2,000,000.00'],
        ]
        self._check(filters.format_currency, testsets)

    def test_02_negative(self):
        testsets = [
            [-200, '($200.00)'],
            [-2000, '($2,000.00)'],
            [-2000000, '($2,000,000.00)'],
        ]
        self._check(filters.format_currency, testsets)
