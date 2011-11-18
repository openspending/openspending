import logging
from collections import defaultdict

from pylons import request, response, app_globals, tmpl_context as c
from pylons.controllers.util import abort

from openspending import model
from openspending.lib import calculator
from openspending.lib import solr_util as solr
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.cache import AggregationCache
from openspending.lib.jsonexport import jsonpify

log = logging.getLogger(__name__)

def statistic_normalize(dataset, result, per, statistic):
    drilldowns = []
    values = {}
    for drilldown in result['drilldown']:
        per_value = drilldown.get(per)
        if not per_value in values:
            entries = list(dataset.entries(dataset.table.c[per]==per_value,
                    limit=1))
            if len(entries):
                values[per_value] = entries[0].get(statistic, 0.0)
            else:
                values[per_value] = 0.0
        if values[per_value]: # skip division by zero oppprtunities
            drilldown['amount'] /= values[per_value]
            drilldowns.append(drilldown)
    result['drilldown'] = drilldowns
    return result

def cellget(cell, key):
    val = cell.get(key)
    if isinstance(val, dict):
        return val.get('name', val.get('id'))
    return val

class ApiController(BaseController):
    @jsonpify
    def index(self):
        out = {
            'doc': 'See %s' % app_globals.api_link
            }
        return out

    def search(self):
        solrargs = dict(request.params)
        rows = min(1000, request.params.get('rows', 10))
        q = request.params.get('q', '*:*')
        solrargs['q'] = q
        solrargs['rows'] = rows
        solrargs['wt'] = 'json'

        datasets = model.Dataset.all_by_account(c.account)
        fq =  ' OR '.join(map(lambda d: '+dataset:"%s"' % d.name, datasets))
        solrargs['fq'] = '(%s)' % fq

        if 'callback' in solrargs and not 'json.wrf' in solrargs:
            solrargs['json.wrf'] = solrargs['callback']
        if not 'sort' in solrargs:
            solrargs['sort'] = 'score desc,amount desc'
        query = solr.get_connection().raw_query(**solrargs)
        response.content_type = 'application/json'
        return query

    @jsonpify
    def aggregate(self):
        dataset_name = request.params.get('dataset', request.params.get('slice'))
        dataset = model.Dataset.by_name(dataset_name)
        require.dataset.read(dataset)

        if dataset is None:
            abort(400, "Dataset %s not found" % dataset_name)

        drilldowns, cuts, statistics = [], [], []
        for key, value in sorted(request.params.items()):
            if not '-' in key:
                continue
            op, key = key.split('-', 1)
            if 'include' == op:
                cuts.append((key, value))
            elif 'per' == op:
                if 'time' == key:
                    abort(400, "Time series are no longer supported")
                statistics.append((key, value))
            elif 'breakdown' == op:
                drilldowns.append(key)
        cache = AggregationCache(dataset)
        result = cache.aggregate(drilldowns=drilldowns + ['time'], 
                                 cuts=cuts)
        #TODO: handle statistics as key-values ??? what's the point?
        for k, v in statistics:
            result = statistic_normalize(dataset, result, v, k)
        # translate to old format: group by drilldown, then by date.
        translated_result = defaultdict(dict)
        for cell in result['drilldown']:
            key = tuple([cellget(cell, d) for d in drilldowns])
            translated_result[key][cell['time']['name']] = \
                    cell['amount']
        dates = sorted(set([d['time']['name'] for d in \
                result['drilldown']]))
        # give a value (or 0) for each present date in sorted order
        translated_result = [(k, [v.get(d, 0.0) for d in dates]) \
                for k, v in translated_result.items()]
        return {'results': translated_result,
                'metadata': {
                    'dataset': dataset.name,
                    'include': cuts,
                    'dates': map(unicode, dates),
                    'axes': drilldowns,
                    'per': statistics,
                    'per_time': []
                    }
                }

    @jsonpify
    def mytax(self):

        def float_param(name, required=False):
            if name not in request.params:
                if required:
                    abort(status_code=400,
                          detail='parameter %s is missing' % name)
                return None
            ans = request.params[name]
            try:
                return float(ans)
            except ValueError:
                abort(status_code=400, detail='%r is not a number' % ans)

        def bool_param(name, default=True, required=False):
            if name not in request.params:
                if required:
                    abort(status_code=400,
                          detail='parameter %s is missing' % name)
                return default

            ans = request.params[name].lower()
            if ans == 'yes':
                return True
            elif ans == 'no':
                return False
            else:
                abort(status_code=400,
                      detail='%r is not %r or %r' % (ans, 'yes', 'no'))

        tax, explanation = calculator.TaxCalculator2010().total_tax(
            float_param('income', required=True),
            float_param('spending'),
            bool_param('smoker'),
            bool_param('drinker'),
            bool_param('driver'))

        result = {'explanation': explanation}
        for k, v in tax.items():
            result[k] = v

        return result
