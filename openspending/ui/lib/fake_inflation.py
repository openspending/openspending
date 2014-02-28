import collections

InflationResult = collections.namedtuple('Inflation', 'factor value')

class Inflation(object):
    def __init__(self, source=None, reference=None, country=None):
        pass

    def get(self, target=None, reference=None, country=None):
        return InflationResult(factor=1.0, value=0.0)

    def inflate(self, amount, target=None, reference=None, country=None):
        return amount
