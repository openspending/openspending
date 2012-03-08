from collections import OrderedDict
import logging

from pylons import request, response
from pylons.controllers.util import abort, etag_cache

from openspending import model
from openspending.lib.jsonexport import jsonpify
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.cache import AggregationCache

log = logging.getLogger(__name__)

class ParamParser(object):
    defaults = OrderedDict({
        'dataset': None,
        'page': 1,
        'pagesize': 10000
    })

    def __init__(self, params):
        self.errors = []

        self.params = self.defaults.copy()
        self.params.update(params)

        self.output = {}

    def parse(self):
        for key in self.params.keys():
            parser = 'parse_{0}'.format(key)
            if hasattr(self, parser):
                result = getattr(self, parser)()
                if result is not None:
                    self.output[key] = result

    def error(self, msg):
        self.errors.append(msg)

    def parse_dataset(self):
        name = self.params['dataset']
        if name is None:
            self.error('dataset name not provided')
            return

        dataset = model.Dataset.by_name(name)
        if dataset is None:
            self.error('no dataset with name "%s"' % name)
            return

        require.dataset.read(dataset)
        return dataset

    def parse_page(self):
        return self._to_int('page')

    def parse_pagesize(self):
        return self._to_int('pagesize')

    def _to_int(self, param_name):
        try:
            return int(self.params[param_name])
        except ValueError:
            self.error('"%s" has to be an integer, it is: %s' %
                       (param_name, self.params[param_name]))

class AggregateParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults.update({
        'drilldown': None,
        'cut': None,
        'order': None,
        'measure': 'amount'
    })

    def parse_drilldown(self):
        drilldown = self.params['drilldown']
        if drilldown is None:
            return []
        return drilldown.split('|')

    def parse_cut(self):
        cut = self.params['cut']

        if cut is None:
            return []

        result = []
        for c in cut.split('|'):
            try:
                dimension, value = cut.split(':')
            except ValueError:
                self.error('Wrong format for "cut". It has to be specified '
                           'with request cut_parameters in the form '
                           '"cut=dimension:value|dimension:value". '
                           'We got: "cut=%s"' %
                           cut)
                return
            else:
                result.append((dimension, value))
        return result

    def parse_order(self):
        order = self.params['order']

        if order is None:
            return []

        result = []
        for part in order.split('|'):
            try:
                dimension, direction = part.split(':')
            except ValueError:
                self.error('Wrong format for "order". It has to be '
                           'specified with request parameters in the form '
                           '"order=dimension:direction|dimension:direction". '
                           'We got: "order=%s"' % order)
                return
            else:
                if direction not in ('asc', 'desc'):
                    self.error('Order direction can be "asc" or "desc". We '
                               'got "%s" in "order=%s"' %
                               (direction, order_param))
                    return

                if direction == 'asc':
                    reverse = False
                else:
                    reverse = True

                result.append((dimension, reverse))
        return result

    def parse_measure(self):
        if self.output.get('dataset') is None:
            return

        name = self.params['measure']

        measure_names = (m.name for m in self.output['dataset'].measures)
        if name not in measure_names:
            print self.output['dataset'].measures
            self.error('no measure with name "%s"' % name)
            return

        return name

class SearchParamParser(ParamParser):
    pass

class Api2Controller(BaseController):

    @jsonpify
    def aggregate(self):
        parser = AggregateParamParser(request.params)
        print parser.defaults
        parser.parse()

        print request.params

        if parser.errors:
            response.status = 400
            return {'errors': parser.errors}

        params = parser.output
        # FIXME: these names should be consistent throughout the API
        params['cuts'] = params.pop('cut')
        params['drilldowns'] = params.pop('drilldown')
        dataset = params.pop('dataset')


        try:
            cache = AggregationCache(dataset)
            result = cache.aggregate(**params)

            if cache.cache_enabled and 'cache_key' in result['summary']:
                if 'Pragma' in response.headers:
                    del response.headers['Pragma']
                response.cache_control = 'public; max-age: 84600'
                etag_cache(result['summary']['cache_key'])

        except (KeyError, ValueError) as ve:
            log.exception(ve)
            response.status = 400
            return {'errors': ['Invalid aggregation query: %r' % ve]}

        return result

    @jsonpify
    def search(self):
        parser = SearchParamParser(request.params)
        parser.parse()

        if parser.errors:
            response.status = 400
            return {'errors': parser.errors}

        params = parser.output
        dataset = params.pop('dataset')

        return {'message': 'APIv2 search endpoint', 'params': params}
