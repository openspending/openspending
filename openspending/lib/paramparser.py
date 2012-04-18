from ordereddict import OrderedDict
from openspending import model

class ParamParser(object):
    defaults = OrderedDict()
    defaults['page'] = 1
    defaults['pagesize'] = 10000
    defaults['order'] = None

    def __init__(self, params):

        self.params = self.defaults.copy()
        self.params.update(params)

    def parse(self):
        self._output = {}
        self._errors = []

        for key in self.params.keys():
            if key not in self.defaults:
                continue

            parser = 'parse_{0}'.format(key)
            if hasattr(self, parser):
                result = getattr(self, parser)(self.params[key])
            else:
                result = self.params[key]

            if result is not None:
                self._output[key] = result

        return self._output, self._errors

    def _error(self, msg):
        self._errors.append(msg)

    def parse_page(self, page):
        return max(1, self._to_float('page', page))

    def parse_pagesize(self, pagesize):
        return self._to_int('pagesize', pagesize)

    def parse_order(self, order):
        if not order:
            return []

        result = []
        for part in order.split('|'):
            try:
                dimension, direction = part.split(':')
            except ValueError:
                self._error('Wrong format for "order". It has to be '
                            'specified with request parameters in the form '
                            '"order=dimension:direction|dimension:direction". '
                            'We got: "order=%s"' % order)
                return
            else:
                if direction not in ('asc', 'desc'):
                    self._error('Order direction can be "asc" or "desc". We '
                                'got "%s" in "order=%s"' %
                                (direction, order))
                    return

                if direction == 'asc':
                    reverse = False
                else:
                    reverse = True

                result.append((dimension, reverse))
        return result

    def _to_float(self, name, value):
        try:
            return float(value)
        except ValueError:
            self._error('"%s" has to be a number, it is: %s' %
                       (name, value))

    def _to_int(self, name, value):
        try:
            return int(value)
        except ValueError:
            self._error('"%s" has to be an integer, it is: %s' %
                       (name, value))

class AggregateParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['dataset'] = None
    defaults['drilldown'] = None
    defaults['cut'] = None
    defaults['order'] = None
    defaults['measure'] = 'amount'

    def parse_dataset(self, dataset_name):
        if not dataset_name:
            self._error('dataset name not provided')
            return

        dataset = model.Dataset.by_name(dataset_name)
        if dataset is None:
            self._error('no dataset with name "%s"' % dataset_name)
            return

        return dataset

    def parse_drilldown(self, drilldown):
        if not drilldown:
            return []
        return drilldown.split('|')

    def parse_cut(self, cuts):
        if not cuts:
            return []

        result = []
        for cut in cuts.split('|'):
            try:
                dimension, value = cut.split(':')
            except ValueError:
                self._error('Wrong format for "cut". It has to be specified '
                            'with request cut_parameters in the form '
                            '"cut=dimension:value|dimension:value". '
                            'We got: "cut=%s"' %
                            cuts)
                return
            else:
                result.append((dimension, value))
        return result

    def parse_measure(self, measure):
        if self._output.get('dataset') is None:
            return

        measure_names = (m.name for m in self._output['dataset'].measures)
        if measure not in measure_names:
            self._error('no measure with name "%s"' % measure)
            return

        return measure

class SearchParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['q'] = ''
    defaults['filter'] = None
    defaults['dataset'] = None
    defaults['page'] = 1
    defaults['pagesize'] = 100
    defaults['order'] = None
    defaults['facet_field'] = None
    defaults['facet_page'] = 1
    defaults['facet_pagesize'] = 100
    defaults['expand_facet_dimensions'] = None

    def parse_filter(self, filter):
        if not filter:
            return {}

        filters = {}
        for f in filter.split('|'):
            try:
                key, value = f.split(':')
            except ValueError:
                self._error('Wrong format for "filter". It has to be '
                            'specified with request parameters in the form '
                            '"filter=key1:value1|key2:value2". '
                            'We got: "filter=%s"' % filter)
                break
            else:
                filters[key] = value

        return filters

    def parse_dataset(self, dataset):
        datasets = []

        if dataset:
            for name in dataset.split('|'):
                dataset = model.Dataset.by_name(name)
                if dataset is None:
                    self._error('no dataset with name "%s"' % name)
                    return
                datasets.append(dataset)

        self._output['filter']['dataset'] = [ds.name for ds in datasets]

        return datasets

    def parse_pagesize(self, pagesize):
        return min(100, self._to_int('pagesize', pagesize))

    def parse_facet_field(self, facet_field):
        if not facet_field:
            return

        return facet_field.split('|')

    def parse_facet_page(self, page):
        return max(1, self._to_float('facet_page', page))

    def parse_facet_pagesize(self, pagesize):
        return min(100, self._to_int('facet_pagesize', pagesize))

    def parse_expand_facet_dimensions(self, expand_facet_dimensions):
        return expand_facet_dimensions is not None


class DistinctParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['q'] = ''
    defaults['page'] = 1
    defaults['pagesize'] = 100

    def __init__(self, params):
        self.params = self.defaults.copy()
        self.params.update(params)

    def parse_pagesize(self, pagesize):
        return min(100, self._to_int('pagesize', pagesize))


class DistinctFieldParamParser(DistinctParamParser):
    defaults = DistinctParamParser.defaults.copy()
    defaults['attribute'] = None

    def __init__(self, dimension, params):
        self.dimension = dimension
        super(DistinctFieldParamParser, self).__init__(params)

    def parse_attribute(self, attribute):
        if not isinstance(self.dimension, model.CompoundDimension):
            return self.dimension
        try:
            return self.dimension[attribute]
        except KeyError:
            return self.dimension['label']
