from pylons import config, request

from openspending import model
from openspending.ui.lib.jsonp import jsonpify
from openspending.ui.lib.base import BaseController

class Api2Controller(BaseController):

    @jsonpify
    def aggregate(self):
        errors = []
        params = request.params

        # get and check parameters
        dataset = self._dataset(params, errors)
        drilldowns = self._drilldowns(params, errors)
        cuts = self._cuts(params, errors)
        order = self._order(params, errors)
        page = self._to_int('page', params.get('page', 1), errors)
        pagesize = self._to_int('pagesize', params.get('pagesize', 10000),
                                errors)
        if errors:
            return {'errors': errors}

        try:
            result = dataset.aggregate(drilldowns=drilldowns, cuts=cuts, page=page, 
                                       pagesize=pagesize, order=order)
        except ValueError:
            return {'errors': ['We cannot aggregate at the moment. '
                               'Please come back later.']}

        return result

    def _dataset(self, params, errors):
        dataset_name = params.get('dataset')
        dataset = model.Dataset.by_name(dataset_name)
        if dataset is None:
            errors.append('no dataset with name "%s"' % dataset_name)
            return
        return dataset

    def _drilldowns(self, params, errors):
        drilldown_param = params.get('drilldown', None)
        if drilldown_param is None:
            return []
        return drilldown_param.split('|')

    def _cuts(self, params, errors):
        cut_param = params.get('cut', None)

        if cut_param is None:
            return []

        cuts = cut_param.split('|')
        result = []
        for cut in cuts:
            try:
                (dimension, value) = cut.split(':')
            except ValueError:
                errors.append('Wrong format for "cut". It has to be specified '
                              'with request cut_parameters in the form '
                              '"cut=dimension:value|dimension:value". '
                              'We got: "cut=%s"' %
                              cut_param)
                return
            else:
                #try:
                #    value = float(value)
                #except:
                #    pass
                result.append((dimension, value))
        return result

    def _order(self, params, errors):
        order_param = params.get('order', None)

        if order_param is None:
            return []

        parts = order_param.split('|')
        result = []
        for part in parts:
            try:
                (dimension, direction) = part.split(':')
            except ValueError:
                errors.append(
                    'Wrong format for "order". It has to be '
                    'specified with request parameters in the form '
                    '"order=dimension:direction|dimension:direction". '
                    'We got: "order=%s"' % order_param)
            else:
                if direction not in ('asc', 'desc'):
                    errors.append('Order direction can be "asc" or "desc". We '
                                  'got "%s" in "order=%s"' %
                                  (direction, order_param))
                    continue
                if direction == 'asc':
                    reverse = False
                else:
                    reverse = True
                result.append((dimension, reverse))
        return result

    def _to_int(self, key, value, errors):
        try:
            return int(value)
        except ValueError:
            errors.append('"%s" has to be an integer, it is: %s' % str(value))
