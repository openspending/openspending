import logging
import urllib2
import json
from collections import defaultdict

from pylons import request, response, app_globals, tmpl_context as c
from pylons.controllers.util import abort

from openspending import model
from openspending.model import Source, Dataset, Account
from openspending.model import meta as db
from openspending.importer import CSVImporter
from openspending.lib import calculator
from openspending.lib import solr_util as solr
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.cache import AggregationCache
from openspending.lib.jsonexport import jsonpify
from openspending.validation.model import validate_model
from openspending.ui.lib.authenticator import ApiKeyAuthenticator


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
            'doc': 'http://openspending.org/help/api.html'
            }
        return out

    def search(self):
        solrargs = dict(request.params)
        rows = min(1000, int(request.params.get('rows', 10)))
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
        try:
            query = solr.get_connection().raw_query(**solrargs)
        except solr.SolrException, se:
            response.status_int = se.httpcode
            return se.body
        response.content_type = 'application/json'
        return query

    @jsonpify
    def aggregate(self):
        dataset_name = request.params.get('dataset', request.params.get('slice'))
        dataset = model.Dataset.by_name(dataset_name)
        if dataset is None:
            abort(400, "Dataset %s not found" % dataset_name)
        require.dataset.read(dataset)

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
    def new(self):
        """
        Adds a new dataset dynamically through a GET request
        """
        # Check if the params are there ('metadata', 'csv_file', 'apikey' and 'signature')
        if len(request.params) != 4:
            abort(status_code=400, detail='incorrect number of params')
        metadata = request.params['metadata'] if 'metadata' in request.params else abort(status_code=400,
                                                                    detail='metadata is missing')
        csv_file = request.params['csv_file'] if 'csv_file' in request.params else abort(status_code=400,
                                                                    detail='csv_file is missing')
        key = request.params['apikey'] if 'apikey' in request.params else abort(status_code=400,
                                                                    detail='apikey is missing')
        
        user_name = ApiKeyAuthenticator().authenticate(environ=None, identity=request.params)
        user = Account.by_name(user_name)
        if not user:
            abort(status_code=400, detail='wrong apikey')

        # The signature is right, we proceed with the dataset
        model = json.load(urllib2.urlopen(metadata))
        try:
            log.info("Validating model")
            model = validate_model(model)
        except Invalid, i:
            log.error("Errors occured during model validation:")
            for field, error in i.asdict().items():
                log.error("%s: %s", field, error)
            abort(status_code=400, detail='Model is not valid')
        dataset = Dataset.by_name(model['dataset']['name'])
        if not dataset:
            dataset = Dataset(model)
            db.session.add(dataset)
        log.info("Dataset: %s", dataset.name)
        source = Source(dataset=dataset, creator=user, url=csv_file)
        log.info(source)
        for source_ in dataset.sources:
            if source_.url == csv_file:
                source = source_
                break
        db.session.add(source)
        db.session.commit()
        dataset.generate()
        importer = CSVImporter(source)
        importer.run()
        solr.build_index(dataset.name)
        return 0

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
